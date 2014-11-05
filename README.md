## Introduction

`workflow.py` is a minimalist file based workflow engine. It runs as a background process and can automate certain tasks such as deleting old files, emailing you when new files are created or run a script to process new files.

## License

3-clause BSD License

Copyright (c) 2012, Massimo Di Pierro
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
- Neither the name of the <organization> nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#### Contributors
- Tim McNamara
- Christoffer
- ivanistheone
- Jonathan Paugh
- Roger Erens

## Configuring and Starting the workflow

- create a file `workflow.config` using the syntax below
- run `workflow.py` in that folder

## Workflow options

- `-f <path>` the folder to monitor and process
- `-s <seconds>` the time interval between checks for new files
- `-n <name>` the current filename, defaults to `$0`
- `-x <path>` the config file to use (workflow.config)
- `-y <path>` the cache file to use (workflow.cache.db)
- `-l <path>` the output logfile (else console output)
- `-d` daemonizes the workflow process
- `-c <rulename>` does not start the workflow but clears a rule (see below)

## `workflow.config` syntax

`workflow.config` consists of a series of rules with the following syntax

    rulename: pattern [dt]: command

where 
- `rulename` is the name of the rule (cannot contain spaces).
- `pattern` is a glob pattern for files to monitor. Avoid using `*.*`!
- `dt` is a time interval (default is 1 second). Only files modified more than `dt` seconds ago will be considered.
- `command` is the command to execute for each file matching `pattern` created more than `dt` seconds ago and not processed already. If the command ends in `&`, it is executed in background, else it blocks the workflow until completion. The name of the matching file can be referred to into the command with `$0`. Multiline commands can be continued with `\`.

Lines starting with `#` are interpreted as comments and ignored.

## Examples of rules

### Delete all `*.log` files older than one day

    delete_old_logs: *.log [1d]: rm $0

### Move all `*.txt` files older than one hour to other folder

    move_old_txt: *.txt [1h]: mv $0 otherfolder/$0

### Email me when a new `*.doc` file is created

    email_me_on_new_doc: *.doc: mail -s 'new file: $0' me@example.com < /dev/null

### Process new `*.dat` files using a Python script

    process_dat: *.dat: python process.py $0

### Create a finite state machine for each `*.src` file

    rule1: *.src [1s]: echo > $0.state.1
    rule2: *.state.1 [1s]: mv $0 `expr "$0" : '\(.*\).1'`.2
    rule3: *.state.2 [1s]: mv $0 `expr "$0" : '\(.*\).2'`.3
    rule4: *.state.3 [1s]: rm $0

## Details

When a file matches a pattern, a new process is created to execute the corresponding command. The pid of the process is saved in `<filename>.<rulename>.pid`. This file is deleted when the process is completed. If the process fails the output log and error is saved in `<filename>.<rulename>.err`. If the process does not fail the output is stored in `<filename>.<rulename>.out`.

If a file has already been processed according to a certain rule, this info is stored in a file `workflow.cache` and it is not processed again unless:

- the mtime of the file changes (for example you edit or touch the file)
- the rule is cleaned up.

You can cleanup a rule with

    python workflow.py -c rulename

This has the effect of creating a file `.workflow.rulename.clear` which the running workflow.py picks up and uses to clear the entry identified by `rulename` in `workflow.cache`, after which the rule will run again.

You can also delete the `workflow.cache` file. In this case all rules will run again when you restart `workflow.py`.

If the main `workflow.py` process is killed or crashes while some commands are being executed, those commands also are killed. You can find which files and rules where being processed by looking for `<filename>.<rulename>.pid` files. If you restart `workflow.py` those pid files are deleted.

If a rule results in an error and a `<filename>.<rulename>.err` is created, the file is not processed again according to the rule, unless the error file is deleted.

If a file is edited or touched and the rule runs again, the `<filename>.<rulename>.out` will be overwritten.

Unless otherwise specified each file is processed 1s after it is last modified. It is possible that a different process is still writing the file but it is pausing more than 1s between writes (for example the file is being downloaded via a slow connection). In this case it is best to download the file with a different name than the name used for the pattern and rename the file to its proper name after the write of the file is completed. This must be handled outside of workflow. Workflow has no way of knowing when a file is completed or not.

If the `workflow.config` file is edited or changed, it is reloaded without the need to re-start `workflow.py`. 
