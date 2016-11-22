###
# Copyright (2016) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###
import unittest
import mock

from hpOneView.oneview_client import OneViewClient
from oneview_storage_volume_attachment import StorageVolumeAttachmentModule, PRESENTATIONS_REMOVED, PROFILE_NOT_FOUND
from test.utils import create_ansible_mock
from test.utils import create_ansible_mock_yaml

FAKE_MSG_ERROR = 'Fake message error'

SERVER_PROFILE_NAME = "SV-1001"

YAML_EXTRA_REMOVED_BY_NAME = """
        config: "{{ config }}"
        state: extra_presentations_removed
        server_profile: "SV-1001"
        """
YAML_EXTRA_REMOVED_BY_URI = """
        config: "{{ config }}"
        state: extra_presentations_removed
        server_profile: "/rest/server-profiles/e6516410-c873-4644-ab93-d26dba6ccf0d"
        """

REPAIR_DATA = {
    "type": "ExtraUnmanagedStorageVolumes",
    "resourceUri": "/rest/server-profiles/e6516410-c873-4644-ab93-d26dba6ccf0d"
}

MOCK_SERVER_PROFILE = {
    "affinity": "BayAndServer",
    "associatedServer": "SGH106X8RN",
    "name": "SV-1001",
    "uri": "/rest/server-profiles/e6516410-c873-4644-ab93-d26dba6ccf0d",
    "sanStorage": {
        "manageSanStorage": True,
        "volumeAttachments": [
            {
                "id": 1,
                "lun": "1",
                "lunType": "Auto",
                "state": "AttachFailed",
                "storagePaths": [
                    {
                        "connectionId": 1,
                        "isEnabled": True,
                        "storageTargets": [
                            "20:00:00:02:AC:00:08:F7"
                        ]
                    }
                ],
                "volumeStoragePoolUri": "/rest/storage-pools/280FF951-F007-478F-AC29-E4655FC76DDC",
                "volumeStorageSystemUri": "/rest/storage-systems/TXQ1010307",
                "volumeUri": "/rest/storage-volumes/89118052-A367-47B6-9F60-F26073D1D85E"
            }
        ]
    },
}


class StorageVolumeAttachmentClientConfigurationSpec(unittest.TestCase):
    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch.object(OneViewClient, 'from_environment_variables')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_load_config_from_file(self, mock_ansible_module, mock_ov_client_from_env_vars,
                                          mock_ov_client_from_json_file):
        mock_ov_instance = mock.Mock()
        mock_ov_client_from_json_file.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock({'config': 'config.json'})
        mock_ansible_module.return_value = mock_ansible_instance

        StorageVolumeAttachmentModule()

        mock_ov_client_from_json_file.assert_called_once_with('config.json')
        mock_ov_client_from_env_vars.not_been_called()

    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch.object(OneViewClient, 'from_environment_variables')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_load_config_from_environment(self, mock_ansible_module, mock_ov_client_from_env_vars,
                                                 mock_ov_client_from_json_file):
        mock_ov_instance = mock.Mock()

        mock_ov_client_from_env_vars.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock({'config': None})
        mock_ansible_module.return_value = mock_ansible_instance

        StorageVolumeAttachmentModule()

        mock_ov_client_from_env_vars.assert_called_once()
        mock_ov_client_from_json_file.not_been_called()


class StorageVolumeAttachmentSpec(unittest.TestCase):
    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_remove_extra_presentation_by_profile_name(self, mock_ansible_module, mock_from_json):
        mock_ov_instance = mock.Mock()
        mock_ov_instance.server_profiles.get_by_name.return_value = MOCK_SERVER_PROFILE
        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.return_value = MOCK_SERVER_PROFILE

        mock_from_json.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock_yaml(YAML_EXTRA_REMOVED_BY_NAME)
        mock_ansible_module.return_value = mock_ansible_instance

        StorageVolumeAttachmentModule().run()

        mock_ov_instance.server_profiles.get_by_name.assert_called_once_with(SERVER_PROFILE_NAME)
        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.assert_called_once_with(REPAIR_DATA)

        mock_ansible_instance.exit_json.assert_called_once_with(
            changed=True,
            msg=PRESENTATIONS_REMOVED,
            ansible_facts=dict(server_profile=MOCK_SERVER_PROFILE)
        )

    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_fail_when_profile_name_not_found(self, mock_ansible_module, mock_from_json):
        mock_ov_instance = mock.Mock()
        mock_ov_instance.server_profiles.get_by_name.return_value = None
        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.return_value = MOCK_SERVER_PROFILE

        mock_from_json.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock_yaml(YAML_EXTRA_REMOVED_BY_NAME)
        mock_ansible_module.return_value = mock_ansible_instance

        StorageVolumeAttachmentModule().run()

        mock_ansible_instance.fail_json.assert_called_once_with(msg=PROFILE_NOT_FOUND)

    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_fail_when_get_profile_by_name_raises_exception(self, mock_ansible_module, mock_from_json):
        mock_ov_instance = mock.Mock()

        mock_ov_instance.server_profiles.get_by_name.side_effect = Exception(FAKE_MSG_ERROR)

        mock_from_json.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock_yaml(YAML_EXTRA_REMOVED_BY_NAME)
        mock_ansible_module.return_value = mock_ansible_instance

        self.assertRaises(Exception, StorageVolumeAttachmentModule().run())

        mock_ansible_instance.fail_json.assert_called_once_with(msg=FAKE_MSG_ERROR)

    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_remove_extra_presentation_by_profile_uri(self, mock_ansible_module, mock_from_json):
        mock_ov_instance = mock.Mock()
        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.return_value = MOCK_SERVER_PROFILE

        mock_from_json.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock_yaml(YAML_EXTRA_REMOVED_BY_URI)
        mock_ansible_module.return_value = mock_ansible_instance

        StorageVolumeAttachmentModule().run()

        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.assert_called_once_with(REPAIR_DATA)

        mock_ansible_instance.exit_json.assert_called_once_with(
            changed=True,
            msg=PRESENTATIONS_REMOVED,
            ansible_facts=dict(server_profile=MOCK_SERVER_PROFILE)
        )

    @mock.patch.object(OneViewClient, 'from_json_file')
    @mock.patch('oneview_storage_volume_attachment.AnsibleModule')
    def test_should_fail_when_remove_raises_exception(self, mock_ansible_module, mock_from_json):
        mock_ov_instance = mock.Mock()

        mock_ov_instance.server_profiles.get_by_name.return_value = MOCK_SERVER_PROFILE
        mock_ov_instance.storage_volume_attachments.remove_extra_presentations.side_effect = Exception(FAKE_MSG_ERROR)

        mock_from_json.return_value = mock_ov_instance
        mock_ansible_instance = create_ansible_mock_yaml(YAML_EXTRA_REMOVED_BY_NAME)
        mock_ansible_module.return_value = mock_ansible_instance

        self.assertRaises(Exception, StorageVolumeAttachmentModule().run())

        mock_ansible_instance.fail_json.assert_called_once_with(msg=FAKE_MSG_ERROR)


if __name__ == '__main__':
    unittest.main()