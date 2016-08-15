# | Copyright 2014-2016 Karlsruhe Institute of Technology
# |
# | Licensed under the Apache License, Version 2.0 (the "License");
# | you may not use this file except in compliance with the License.
# | You may obtain a copy of the License at
# |
# |     http://www.apache.org/licenses/LICENSE-2.0
# |
# | Unless required by applicable law or agreed to in writing, software
# | distributed under the License is distributed on an "AS IS" BASIS,
# | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# | See the License for the specific language governing permissions and
# | limitations under the License.

import os, sys, logging
from grid_control.config.cfiller_base import CompatConfigFiller, DefaultFilesConfigFiller, DictConfigFiller, GeneralFileConfigFiller, MultiConfigFiller
from grid_control.config.cinterface_typed import SimpleConfigInterface
from grid_control.config.config_entry import ConfigContainer, ConfigError
from grid_control.config.cview_base import SimpleConfigView
from grid_control.gc_exceptions import GCLogHandler
from grid_control.utils import ensureDirExists, getRootName, resolvePath
from grid_control.utils.data_structures import UniqueList
from grid_control.utils.file_objects import SafeFile
from python_compat import lfilter

# Main config interface
class ConfigFactory(object):
	def __init__(self, filler = None, configFilePath = None):
		def getName(prefix = ''):
			if configFilePath:
				return ('%s.%s' % (prefix, getRootName(configFilePath))).strip('.')
			elif prefix:
				return prefix
			return 'unnamed'

		try:
			pathMain = os.getcwd()
		except Exception:
			raise ConfigError('The current directory does not exist!')
		if configFilePath:
			pathMain = os.path.dirname(resolvePath(configFilePath,
				searchPaths = [os.getcwd()], ErrorClass = ConfigError))

		# Init config containers
		self._curContainer = ConfigContainer('current')
		if filler: # Read in the current configuration ...
			filler.fill(self._curContainer)
		self._curContainer.resolve() # resolve interpolations

		logging.getLogger('config.stored').propagate = False
		oldContainer = ConfigContainer('stored')
		oldContainer.enabled = False

		# Create config view and temporary config interface
		self._view = SimpleConfigView(getName(), oldContainer, self._curContainer)
		self._view.pathDict['search_paths'] = UniqueList([os.getcwd(), pathMain])

		# Determine work directory using config interface with "global" scope
		tmp_config = SimpleConfigInterface(self._view.getView(setSections = ['global']))
		wdBase = tmp_config.getPath('workdir base', pathMain, mustExist = False)
		pathWork = tmp_config.getPath('workdir', os.path.join(wdBase, getName('work')), mustExist = False)
		self._view.pathDict['<WORKDIR>'] = pathWork # tmp_config still has undefinied
		# Set dynamic plugin search path
		sys.path.extend(tmp_config.getPaths('plugin paths', [os.getcwd()]))

		# Determine and load stored config settings
		self._flatCfgPath = os.path.join(pathWork, 'current.conf') # Minimal config file
		self._oldCfgPath = os.path.join(pathWork, 'work.conf') # Config file with saved settings
		if os.path.exists(self._oldCfgPath):
			GeneralFileConfigFiller([self._oldCfgPath]).fill(oldContainer)
			CompatConfigFiller(os.path.join(pathWork, 'task.dat')).fill(oldContainer)
			oldContainer.enabled = True
			oldContainer.setReadOnly()

		# Get persistent variables - only possible after oldContainer was enabled
		self._view.setConfigName(tmp_config.get('config id', getName(), persistent = True))


	def getConfig(self):
		result = SimpleConfigInterface(self._view)
		result.factory = self
		return result


	def _write_file(self, fn, message = None, **kwargs):
		fp = SafeFile(fn, 'w')
		if message is not None:
			fp.write(message)
		self._view.write(fp, **kwargs)
		fp.close()


	def freezeConfig(self, writeConfig = True):
		self._curContainer.setReadOnly()
		# Inform the user about unused options
		unused = lfilter(lambda entry: ('!' not in entry.section) and not entry.accessed, self._view.iterContent())
		log = logging.getLogger('config.freeze')
		if unused:
			log.log(logging.INFO1, 'There are %s unused config options!', len(unused))
		for entry in unused:
			log.log(logging.INFO1, '\t%s', entry.format(printSection = True))
		if writeConfig or not os.path.exists(self._oldCfgPath):
			ensureDirExists(os.path.dirname(self._oldCfgPath), 'config storage directory', ConfigError)
			# Write user friendly, flat config file and config file with saved settings
			self._write_file(self._flatCfgPath, printDefault = False, printUnused = False, printMinimal = True,
				printWorkdir = True)
			self._write_file(self._oldCfgPath,  printDefault = True,  printUnused = True,  printMinimal = True, printSource = True,
				message = '; ==> DO NOT EDIT THIS FILE! <==\n; This file is used to find config changes!\n')


def createConfig(configFile = None, configDict = None, useDefaultFiles = True, additional = None, register = False):
	fillerList = []
	if useDefaultFiles:
		fillerList.append(DefaultFilesConfigFiller())
	if configFile:
		fillerList.append(GeneralFileConfigFiller([configFile]))
	if configDict:
		fillerList.append(DictConfigFiller(configDict))
	fillerList.extend(additional or [])
	config = ConfigFactory(MultiConfigFiller(fillerList), configFile).getConfig()
	if register:
		GCLogHandler.config_instances.append(config)
	return config
