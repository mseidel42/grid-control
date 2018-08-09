# | Copyright 2010-2017 Karlsruhe Institute of Technology
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

from grid_control.utils import Result, get_path_share
from grid_control_cms.task_cmssw_advanced import CMSSWAdvanced


class CMSSWLight(CMSSWAdvanced):  # pylint:disable=too-many-ancestors
	alias_list = ['CMSSW_Light']
	config_section_list = CMSSWAdvanced.config_section_list + ['CMSSW_Light']

	def __init__(self, config, name):

		super(CMSSWLight, self).__init__(config, name)
		self._script_fpi = Result(path_rel='gc-run.cmssw-light.sh',
			path_abs=get_path_share('gc-run.cmssw-light.sh', pkg='grid_control_cms'))
		self._update_map_error_code2msg(
			get_path_share('gc-run.cmssw-light.sh', pkg='grid_control_cms'))

	def get_command(self):
		return './gc-run.cmssw-light.sh $@'
