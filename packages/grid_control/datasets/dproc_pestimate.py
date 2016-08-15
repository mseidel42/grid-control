# | Copyright 2016 Karlsruhe Institute of Technology
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

from grid_control.datasets.dproc_base import DataProcessor
from grid_control.datasets.provider_base import DataProvider
from python_compat import identity, ifilter, lmap

class PartitionEstimator(DataProcessor):
	alias = ['estimate', 'SplitSettingEstimator']

	def __init__(self, config, onChange):
		DataProcessor.__init__(self, config, onChange)
		self._targetJobs = config.getInt('target partitions', -1, onChange = onChange)
		self._targetJobsDS = config.getInt('target partitions per nickname', -1, onChange = onChange)
		self._entries = {None: 0}
		self._files = {None: 0}
		self._config = config

	def enabled(self):
		return (self._targetJobs != -1) or (self._targetJobsDS != -1)

	def _setSplitParam(self, config, name, value):
		config.setInt(name, max(1, int(value / float(self._targetJobs) + 0.5)))

	def process(self, blockIter):
		if (self._targetJobs != -1) or (self._targetJobsDS != -1):
			blocks = lmap(self.processBlock, blockIter)
			if self._targetJobs:
				self._setSplitParam(self._config, 'files per job', self._files[None])
				self._setSplitParam(self._config, 'events per job', self._entries[None])
			if self._targetJobsDS:
				for nick in ifilter(identity, self._files):
					block_config = self._config.changeView(setSections = ['dataset %s' % nick])
					self._setSplitParam(block_config, 'files per job', self._files[nick])
					self._setSplitParam(block_config, 'events per job', self._entries[nick])
			return blocks
		else:
			return blockIter

	def processBlock(self, block):
		def inc(key):
			self._files[key] = self._files.get(key, 0) + len(block[DataProvider.FileList])
			self._entries[key] = self._entries.get(key, 0) + block[DataProvider.NEntries]
		inc(None)
		if block.get(DataProvider.Nickname):
			inc(block.get(DataProvider.Nickname))
		return block
