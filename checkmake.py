import tarfile
import sys
import subprocess
import os
import shutil
import getopt

WORKING_DIR         = "./work"
STDOUT_FILE         = "make.stdout"
STDERR_FILE         = "make.stderr"
LOG_FILE            = "checkmake.out"
REMOVE_WORK_DEFAULT = True

class Options():
    pass

class Log():
    NONE    = 0
    FATAL   = 1
    ERROR   = 2
    WARNING = 3
    INFO    = 4
    DEBUG   = 5
    ALL     = 6
    levels  = [ "NONE", "FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "ALL" ]
    level_map = {}
    
    def __init__( self, filename, log_level_console=WARNING, log_level_file=INFO ):
        self.file = open( filename, "w" )
        self.file_level    = log_level_file
        self.console_level = log_level_console
        for n in range(Log.ALL):
            level_map = { n, self.levels[n] }

    def __del__(self):
        self.file.close()

    # TODO: figure out how to use Log.INFO below rather than 3
    def print( self, *args, sep=' ', end='\n', level=3 ):
        level_text = Log.levels[level] + ":"

        if level <= self.file_level:
            print( level_text, *args, file=self.file, sep=sep, end=end )
        if level <= self.console_level:
            print( level_text, *args, sep=sep, end=end )
            

    def debug( self, *args, sep=' ', end='\n' ):
        self.print( *args, sep=sep, end=end, level=Log.DEBUG )

    def info( self, *args, sep=' ', end='\n' ):
        self.print( *args, sep=sep, end=end, level=Log.INFO )

    def warning( self, *args, sep=' ', end='\n' ):
        self.print( *args, sep=sep, end=end, level=Log.WARNING )

    def error( self, *args, sep=' ', end='\n' ):
        self.print( *args, sep=sep, end=end, level=Log.ERROR )

    @classmethod
    def code_to_level( cls, level_text ):
        index = cls.levels.index(level_text)
        return index
    
        

def path_is_parent(parent_path, child_path):
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)
    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])

        
def test_tarball( log, tarball, working_dir ):

    log.info( "Expanding tarball:", tarball, "into", working_dir )
    
    project_dir = working_dir
    
    try:
        tar = tarfile.open( tarball, "r:gz") 
        top = tar.getmembers()[0]
        if top.type == tarfile.DIRTYPE: 
            project_dir = project_dir + "/" + top.name
            log.info( "Top level of the tarball is the directory:", top.name )
        else:
            log.warning( "Warning: top member of the tarball is not a directory. Rolling with it anyway." )
        tar.extractall( path = WORKING_DIR )

    except Exception as err:
        log.error( "Error expanding the tarball:", err )
        return None

    log.info( "Project dir is set to:", project_dir )
    
    return project_dir

def test_make( log, project_dir, stdout_file, stderr_file ):
    cwd = os.getcwd()
    
    
    os.chdir( project_dir )

    log.info( "Running makefile" )

    result = subprocess.run(["make"], capture_output=True, text=True)

    level = Log.INFO
    
    if result.returncode != 0:
        level = Log.ERROR

    
    log.print( "make failed with return code:", result.returncode, level = level )
    log.print( "stdout ---------------------", level = level )
    log.print( result.stdout, level = level )
    log.print( "stderr ---------------------", level = level )
    log.print( result.stderr, level = level )
        
    os.chdir( cwd )

    # write output files
    f = open( stdout_file, "w" )
    f.write( result.stdout )
    f.close()
    
    f = open( stderr_file, "w" )
    f.write( result.stderr )
    f.close()

    return result.returncode == 0

def test_readme( log, project_dir ):

    readme = project_dir + "/" + "README.txt"

    try:
        stat = os.stat( readme )
        if stat.st_size == 0:
            log.error( "README.txt exists but it is empty" )
            return False
        
    except Exception as e:
        log.error( "README.txt not found:", e )
        return False


    return True

def test_target( log, project_dir, target ):

    target_file = project_dir + "/" + target

    try:
        stat = os.stat( target_file )
    except Exception as e:
        log.error( "Target file", target, "not found:", e )
        return False


    return True

def handle_args():
    options = Options()
    opts = []
    args = []
    
    try:
        opts, args = getopt.gnu_getopt( sys.argv[1:], "xo:e:hw:l:t:",
                                        [ "stdout=", "stderr=", "help", "work=", "log=", "flog_level=", "clog_level=", "target=" ] )
    except getopt.GetoptError as err:
        print( err )
        sys.exit(1)

    options.remove_work       = REMOVE_WORK_DEFAULT
    options.stderr_file       = ""
    options.stdout_file       = ""
    options.working_dir       = WORKING_DIR
    options.log_file          = ""
    options.args              = args
    options.preserve_work     = False
    options.verbose           = 1
    options.log_level_file    = Log.INFO
    options.log_level_console = Log.WARNING
    options.target            = ""
    
    for o, a in opts:
        if o == "-x":
            options.preserve_work = False
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--stdout"):
            options.stdout_file = a
        elif o in ("-e", "--STDERR_FILE"):
            options.stderr_file = a
        elif o in ("-w", "--work"):
            options.working_dir = a
        elif o in ("-l", "--log"):
            options.log_file = a
        elif o in ("-t", "--target"):
            options.target = a
        elif o in ("--flog_level", "--clog_level" ):
            try:
                level = Log.code_to_level( a )
                if o == "--flog_level":
                    options.log_level_file = level
                else:
                    options.log_level_console = level
            except:
                print( "Invalid log level:", a )
                sys.exit(1)
        else:
            assert False, "unhandled option"

        
    if options.stdout_file == "":
        options.stdout_file = options.working_dir + "/" + STDOUT_FILE
    if options.stderr_file == "":
        options.stderr_file = options.working_dir + "/" + STDERR_FILE
    if options.log_file == "":
        options.log_file = options.working_dir + "/" + LOG_FILE
                    
    options.tarball = args[0]

    return options


def main():

    opts = handle_args()


    if path_is_parent( ".", opts.working_dir ) == False:
        print( "The working directory must be a child of the current directory" )
        print( "This is to help keep you from accidentally blowing away your system" )
        sys.exit(1)

    # Remove the working dir before we start unless told not to
    if opts.preserve_work == False:
        shutil.rmtree( opts.working_dir, ignore_errors=True )

    os.mkdir( opts.working_dir )

    log = Log( opts.log_file,
               log_level_console=opts.log_level_console,
               log_level_file=opts.log_level_file )


    log.info( "Starting" )
    
    project_dir = test_tarball( log, opts.tarball, opts.working_dir )

    if project_dir == None:
        print( "Error calling explode_tarball" )
        sys.exit(1)

    ret = test_make( log, project_dir, opts.stdout_file, opts.stderr_file )
    if ret == False:
        log.error( "test_make failed" )
        sys.exit(1)
    
    ret = test_readme( log, project_dir )
    if ret == False:
        log.error( "test_readme failed" )
        sys.exit(1)

    if opts.target != "":
        ret = test_target( log, project_dir, opts.target )
        if ret == False:
            log.error( "test_readme failed" )
            sys.exit(1)
        
    # Remove the working dir when done if asked to
    if opts.remove_work == False:
        shutil.rmtree( opts.working_dir, ignore_errors=True )


    
    
if __name__ == "__main__":
    main()








        
