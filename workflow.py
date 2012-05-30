import sys, os, shelve, glob, time, shlex, subprocess, logging, re, optparse

re_line = re.compile('(?P<n>\w+):\s*(?P<p>.+?)\s*(\[(?P<dt>\w+)\]\s*)?:\s*(?P<c>.*)\s*(?P<a>\&)?')

def load_config(config_filename,data):
    if not os.path.exists(config_filename): return (None,0)
    config_mt = os.path.getmtime(config_filename)
    config = []
    print '-'*10+' loading rules '+'-'*10
    for line in open(config_filename,'r').read().replace('\\','\n').split('\n'):
        if not line.startswith('#') and ':' in line:
            match = re_line.match(line)
            if match:
                print line
                name = match.group('n')
                pattern = match.group('p')
                dt = eval((match.group('dt') or '1').replace('s','*1').replace('m','*60').replace('h','*3600').replace('d','*24*3600').replace('w','*7*24*3600'))
                command = match.group('c')
                ampersand = match.group('a')
            config.append((name,pattern,dt,command,ampersand))
            if not name in data:
                data[name]=[]
    return config, config_mt

def workflow(options):
    folder = options.folder or './'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(levelname)-8s: %(message)s',
                        datefmt='%m-%d %H:%M')
    config_filename = os.path.join(folder,'workflow.config')
    cache_filename = os.path.join(folder,'workflow.cache')
    data = shelve.open(cache_filename)
    if options.clear:
        for key in data.get(options.clear,[]):
            del data[key]
        return
    config, config_mt = load_config(config_filename,data)
    processes = {}
    print '-'*10+' looping '+'-'*10
    while config:
        if config_mt < os.path.getmtime(config_filename):
            config, config_mt = load_config(config_filename,data)
        if not config: return
        for name,pattern,dt,action,ampersand in config:
            filenames = glob.glob(pattern)
            for filename in filenames:
                mt = os.path.getmtime(filename)
                if mt > time.time()-dt: continue
                pid_file = filename+'.%s.pid' % name                
                log_file = filename+'.%s.out' % name
                err_file = filename+'.%s.err' % name
                key = re.sub('\s+',' ',pattern+'='+filename+':'+action).strip()
                if not os.path.exists(pid_file) and not os.path.exists(err_file):
                    if data.get(key,None)!=mt:  
                        command = action.replace(options.name,filename)
                        logging.info('%s -> %s' % (filename, command))
                        wlg = open(log_file,'wb')
                        process = subprocess.Popen(command,stdout=wlg,
                                                   stderr=wlg,shell=True)
                        if not ampersand: process.wait()
                        open(pid_file,'w').write(str(process.pid))
                        processes[pid_file] = (filename,command,process)
                elif pid_file in processes and processes[pid_file][2].poll()==0:
                    filename, command, process = processes[pid_file]
                    returncode = process.returncode
                    if returncode !=0:
                        open(err_file,'w').write(str(returncode))                    
                        logging.error('%s -> %s' % (filename, command))
                    else:
                        data[key] = mt
                        data[name] = data[name]+[key]
                    del processes[pid_file]
                    os.remove(pid_file)
                elif os.path.exists(pid_file) and not pid_file in processes:
                    os.remove(pid_file)
            time.sleep(options.sleep)

def main():
    usage = """ ... """
    version = "0.1"
    parser = optparse.OptionParser(usage, None, optparse.Option, version)
    parser.add_option("-s", "--sleep", dest="sleep",default=1,
                      help="sleep interval")
    parser.add_option("-c", "--clear", dest="clear",default=None,
                      help="clear rule")
    parser.add_option("-n", "--name", dest="name",default='$0',
                      help="name")
    parser.add_option("-f", "--folder", dest="folder",default=None,
                      help="folder for workflow")
    (options, args) = parser.parse_args()
    workflow(options)
    

if __name__=='__main__': main()