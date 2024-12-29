#!/usr/bin/python

# ANSIBLE_LIBRARY=./library ansible -m sysdumpdev -a 'copy_directory=/var/adm/ras forced_copy_flag=True dump_type=fw-assisted dump_mode=disallow' localhost

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: sysdumpdev

short_description: Manage system dump settings

version_added: "1.0.0"

description: This module allows to update and display the system dump settings using the sysdumpdev command

options:
    state:
        description: 
        - Specifies the action to be performed
        - C(present) specifies to update the system dump settings
        - C(info) specifies to retrieve the current system dump settings
        choices: ['present', 'info']
        default: info
        type: str
    primary:
        description:
            - Specifies the primary dump device
        type: str
    secondary:
        description:
            - Specifies the secondary dump device
        required: false
        type: str
    permanent:
        description:
            - Makes updates to the O(primary) or O(secondary) dump device setting permanent
        type: bool
    copy_directory:
        description:
            - Specifies the directory to where the dump is copied to at system boot
        required: false
        type: str
    forced_copy_flag:
        description:
            - If set to V(true) specifies to copy the system dump to an external media if the copy fails at boot time.
            - If set to V(false) specifies to ignore the system dump if the copy fails at boot time.
            - Requires the O(copy_directory) option to be specified
        type: bool
    always_allow_dump:
        description:
            - If set to V(true) and if your machine has a key mode switch, the reset button or the dump key sequences will force a dump with the key in the normal position.
            - If set to V(false) and if your machine has a key mode switch, it is required to be in the service position before a dump can be forced with the dump key sequences.
        required: false
        type: bool
    dump_type:
        description:
             - Specifies whether a traditional or fw-assisted system dump is performed
        required: false
        choices: ['traditional', 'fw-assisted']
        type: str
    dump_mode:
        description:
            - Specifies the dump mode
            - C(disallow) specifies that neither the full memory system dump mode nor the kernel memory system dump mode is allowed. It is the selective memory mode.
            - C(allow_full) specifies that the full memory system dump mode is allowed but is performed only when operating system cannot properly handle the dump request.
            - C(require_full) specifies that the full memory system dump mode is allowed and is always performed.
            - Requires the O(dump_type=fw-assisted) option to be specified
        required: false
        choices: ['disallow', 'allow', 'allow_kernel', 'require_kernel', 'allow_full', 'require_full']
        type: str

notes: 
    - You can refer to the IBM documentation for additional information on the commands used at
      U(https://www.ibm.com/docs/en/aix/7.3?topic=s-sysdumpdev-command)
      U(https://www.ibm.com/docs/en/aix/7.2?topic=s-sysdumpdev-command)

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Oliver Stadler (@staoli)
'''

EXAMPLES = r'''
- name: Configure primary and secondary dump devices permanently
  ibm.power_aix.sysdumpdev:
      primary: /dev/sysdump0
      secondary: /dev/sysdump1
      permanent: True

- name: Configure system dump copy directory and set the forced copy flag to False
  ibm.power_aix.sysdumpdev:
       copy_directory: /var/adm/ras
       forced_copy_flag: True

- name: Configure fw-assisted and allow full memory system dump mode always be performed.
  ibm.power_aix.sysdumpdev:
       dump_type: fw-assisted
       dump_mode: require_full

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
command:
    description: The sysdumpdev command which was executed
    type: str
    returned: always
    sample: 'sysdumpdev -D /var/adm/ras'
sysdumpdev_config:
    description: The current sysdumpdev settings
    type: dict
    returned: If O(state=info) is specified
    sample: '"sysdumpdev_config": {
                "always_allow_dump": true,
                "copy_diretory": "/var/adm/ras",
                "dump_compression": true,
              }'
msg:
    description: The execution message.
    returned: always
    type: str
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: always
    type: str
stderr:
    description: The standard error.
    returned: always
    type: str
#- stdout
#        The command standard output.
#        returned: always
#        sample: "Clustering node rabbit@slave1 with rabbit@master \u2026"
#        type: str
#
#- stdout_lines
#        The command standard output split in lines.
#        returned: always
#        sample: ["u'Clustering node rabbit@slave1 with rabbit@master \u2026'"]
#        type: list
#
'''

#    result = dict(
#        changed=False,
#        command='',
#        stdout='',
#        stderr='',
#        sysdumpdev_config='',
from ansible.module_utils.basic import AnsibleModule

def get_dump_config(module):
    sysdumpdev_command = module.get_bin_path('sysdumpdev', required=True)
    cmd = [sysdumpdev_command, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run sysdumpdev command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    # Strip newline and double-quotation marks that are sometimes added
    #sysdumpdev_out = stdout.splitlines()[1].split(':', 1)[1].strip('\\\"\n')

    # # sysdumpdev -l
    # primary              /dev/lg_dumplv
    # secondary            /dev/dump1
    # copy directory       /var/adm/ras
    # forced copy flag     TRUE
    # always allow dump    FALSE
    # dump compression     ON
    # type of dump         fw-assisted
    # full memory dump     disallow
    # enable NX GZIP       TRUE

    dump_config = {}
    for line in stdout.splitlines():
        if line.startswith('primary'):
            dump_config['primary'] = line.split()[-1]
        if line.startswith('secondary'):
            dump_config['secondary'] = line.split()[-1]
        if line.startswith('copy directory'):
            dump_config['copy_directory'] = line.split()[-1]
        if line.startswith('forced copy flag'):
            dump_config['forced_copy_flag'] = line.split()[-1]
        if line.startswith('always allow dump'):
            dump_config['always_allow_dump'] = line.split()[-1]
        if line.startswith('dump compression'):
            dump_config['dump_compression'] = line.split()[-1]
        if line.startswith('type of dump'):
            dump_config['dump_type'] = line.split()[-1]
        if line.startswith('full memory dump'):
            dump_config['dump_mode'] = line.split()[-1]
        if line.startswith('enable NX GZIP'):
            dump_config['nx_gzip'] = line.split()[-1]

    for a in dump_config.keys():
        if isinstance(dump_config[a], str) and dump_config[a] == 'TRUE':
            dump_config[a] = True
        if isinstance(dump_config[a], str) and dump_config[a] == 'FALSE':
            dump_config[a] = False
        if isinstance(dump_config[a], str) and dump_config[a] == 'ON':
            dump_config[a] = True
        if isinstance(dump_config[a], str) and dump_config[a] == 'OFF':
            dump_config[a] = False

    return dict(dump_config)

def set_dump_config(module, cmd_args):
    sysdumpdev_command = module.get_bin_path('sysdumpdev', required=True)
    cmd = [sysdumpdev_command] + cmd_args
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run sysdumpdev command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    return_dict = {
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    return return_dict


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=False, choices=['present', 'info'], default='info'),
        primary=dict(type='path', required=False),
        secondary=dict(type='path', required=False),
        permanent=dict(type='bool', required=False),
        copy_directory=dict(type='path', required=False),
        forced_copy_flag=dict(type='bool', required=False),
        always_allow_dump=dict(type='bool', required=False),
        dump_type=dict(type='str', required=False, choices=['traditional', 'fw-assisted']),
        dump_mode=dict(type='str', required=False, choices=['disallow', 'allow', 'allow_kernel', 'require_kernel', 'allow_full', 'require_full'])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        command='',
        stdout='',
        stderr='',
        sysdumpdev_config='',
        original_config=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
          ('permanent', True, ['primary', 'secondary'], True),
          ('dump_type', 'fw-assisted', ['dump_mode'])
        ],
        required_together=[
          [ 'forced_copy_flag', 'copy_directory']
        ]
          #('forced_copy_flag', True, ['copy_directory']),
    )

    # Check if the 'dump_type' is 'fw-assisted' when 'dump_mode' is specified.
    if module.params.get('dump_mode') and module.params.get('dump_type') != 'fw-assisted':
        module.fail_json(msg="If 'dump_mode' is specified, 'dump_type' must be 'fw-assisted'.")

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    current_config = get_dump_config(module)

    if module.params['state'] == 'info':
      result['sysdumpdev_config'] = current_config 
    else:
      result['original_config'] = current_config 

      cmd_args = []

      if module.params['primary'] is not None and ( module.params['primary'] != current_config['primary'] ):
          cmd_args.append('-p')
          cmd_args.append(module.params['primary'])
          result['changed'] = True

      if module.params['secondary'] is not None and ( module.params['secondary'] != current_config['secondary'] ):
          cmd_args.append('-s')
          cmd_args.append(module.params['secondary'])
          result['changed'] = True

      if module.params['permanent']:
          cmd_args.append('-P')

      target_copy_directory = current_config['copy_directory']
      target_forced_copy_flag = current_config['forced_copy_flag']
      copy_directory_change = False
      forced_copy_flag_change = False

      if module.params['copy_directory'] is not None and (module.params['copy_directory'] != current_config['copy_directory']):
          copy_directory_change = True
          target_copy_directory = module.params['copy_directory']

      if module.params['forced_copy_flag'] is not None and (module.params['forced_copy_flag'] != current_config['forced_copy_flag']):
          forced_copy_flag_change = True
          target_forced_copy_flag = module.params['forced_copy_flag']

      if copy_directory_change or forced_copy_flag_change:
          if target_forced_copy_flag == True:
              cmd_args.append('-D')
          else:
              cmd_args.append('-d')
          result['changed'] = True
          cmd_args.append(target_copy_directory)

      if module.params['always_allow_dump'] is not None:
          if module.params['always_allow_dump']:
              cmd_args.append('-K')
          else:
              cmd_args.append('-k')

      if module.params['dump_type'] is not None and (module.params['dump_type'] != current_config['dump_type']) :
          cmd_args.append('-t')
          cmd_args.append(module.params['dump_type'])
          result['changed'] = True

      if module.params['dump_mode'] is not None:
        if current_config['dump_type'] != 'fw-assisted':
          module.fail_json(msg='dump_type must be fw-assisted before you configure dump_mode', **result)
        elif ( current_config['dump_type'] == 'fw-assisted' ) and ( module.params['dump_mode'] != current_config['dump_mode']):
          cmd_args.append('-f')
          cmd_args.append(module.params['dump_mode'])
          result['changed'] = True

      if result['changed']:
        set_dump_result = set_dump_config(module, cmd_args)
        result['command'] = set_dump_result['cmd']
        result['original_config'] = current_config

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    #if module.params['primary']:
    #    result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['primary'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
