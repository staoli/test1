#!/usr/bin/python

# ANSIBLE_LIBRARY=./library ansible -m sysdumpdev -a 'copy_directory=/var/adm/ras forced_copy_flag=True dump_type=fw-assisted dump_mode=disallow' localhost

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

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

    for a in dump_config.keys():
        if isinstance(dump_config[a], str) and dump_config[a] == 'TRUE':
            dump_config[a] = True
        if isinstance(dump_config[a], str) and dump_config[a] == 'FALSE':
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

    #if module.params['copy_directory'] is not None and (module.params['copy_directory'] != current_config['copy_directory']):
    #    if module.params['forced_copy_flag'] == True:
    #        cmd_args.append('-D')
    #    else:
    #        cmd_args.append('-d')
    #    result['changed'] = True
    #    cmd_args.append(module.params['copy_directory'])

    #if module.params['forced_copy_flag'] is not None and (module.params['forced_copy_flag'] != current_config['forced_copy_flag']):
    #    if module.params['forced_copy_flag'] == True:
    #        cmd_args.append('-D')
    #    else:
    #        cmd_args.append('-d')
    #    result['changed'] = True
    #    cmd_args.append(module.params['copy_directory'])

        #forced_copy_flag=dict(type='bool', required=False),

    if module.params['always_allow_dump'] is not None:
        if module.params['always_allow_dump']:
            cmd_args.append('-K')
        else:
            cmd_args.append('-k')

    if module.params['dump_type'] is not None and (module.params['dump_type'] != current_config['dump_type']) :
        cmd_args.append('-t')
        cmd_args.append(module.params['dump_type'])
        result['changed'] = True

    #if module.params['dump_mode'] is not None and ( current_config['dump_type'] == 'fw-assisted') and (module.params['dump_mode'] != current_config['dump_mode']) :
    #if module.params['dump_mode'] is not None:
    #if module.params['dump_mode'] is not None and (module.params['dump_mode'] != current_config['dump_mode']):

    change_dump_mode = False
    if current_config['dump_type'] != 'fw-assisted':
      module.fail_json(msg='dump_type must be fw-assisted before you configure dump_mode', **result)
      if module.params['dump_mode'] is not None:
          if 'dump_mode' in current_config.keys():
            if module.params['dump_mode'] != current_config['dump_mode']:
              change_dump_mode = True
              #cmd_args.append('-f')
              #cmd_args.append(module.params['dump_mode'])
              #result['changed'] = True
          else:
              change_dump_mode = True
              #cmd_args.append('-f')
              #cmd_args.append(module.params['dump_mode'])
              #result['changed'] = True

          if change_dump_mode:
              cmd_args.append('-f')
              cmd_args.append(module.params['dump_mode'])
              result['changed'] = True

    if result['changed']:
      set_dump_result = set_dump_config(module, cmd_args)
      result['command'] = set_dump_result['cmd']
      #result['stdout'] = set_dump_result['stdout']
      #result['stderr'] = set_dump_result['stderr']
      result['original_config'] = current_config

        #result['command'] = 'not none'
        #module.fail_json(msg='You requested this to fail', **result)
    #else:
    #    result['command'] = 'was none'
    #if module.params['always_allow_dump']:
    #    result['command'] = 'was'
    #else:
    #    result['command'] = 'was not'

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
