import tarfile
import sys
import subprocess
import os
import shutil
import getopt
from dataclasses import dataclass, field

VERSION             = "1.0.0"
WORKING_DIR         = "./work"
STDOUT_FILE         = "make.stdout"
STDERR_FILE         = "make.stderr"
LOG_FILE            = "checkmake.out"
REMOVE_WORK_DEFAULT = True

class Log:
    NONE    = 0
    FATAL   = 1
    ERROR   = 2
    WARNING = 3
    INFO    = 4
    DEBUG   = 5
    ALL     = 6

    levels = ["NONE", "FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "ALL"]
    
    def __init__(self, filename, log_level_console=WARNING, log_level_file=INFO):
        """
        Initialize the Log class with file logging and console logging levels.
        
        Parameters:
            filename (str): The file to which log messages will be written.
            log_level_console (int): Minimum log level for messages to be printed to the console.
            log_level_file (int): Minimum log level for messages to be written to the file.
        """
        self.file = open(filename, "w")
        self.file_level = log_level_file
        self.console_level = log_level_console

    def __del__(self):
        """Close the log file upon deletion of the Log object."""
        if self.file and not self.file.closed:
            self.file.close()

    def print(self, *args, sep=' ', end='\n', level=INFO):
        """
        Print a log message to the console and/or file based on the log level.
        
        Parameters:
            *args: The log message components.
            sep (str): Separator between log message components (default: ' ').
            end (str): End character for the log message (default: '\n').
            level (int): The log level of the message (default: INFO).
        """
        if level < Log.NONE or level > Log.ALL:
            raise ValueError(f"Invalid log level: {level}")

        level_text = f"{Log.levels[level]}:"

        if level <= self.file_level:
            print(level_text, *args, file=self.file, sep=sep, end=end)
        if level <= self.console_level:
            print(level_text, *args, sep=sep, end=end)

    def debug(self, *args, sep=' ', end='\n'):
        """Log a debug message."""
        self.print(*args, sep=sep, end=end, level=Log.DEBUG)

    def info(self, *args, sep=' ', end='\n'):
        """Log an info message."""
        self.print(*args, sep=sep, end=end, level=Log.INFO)

    def warning(self, *args, sep=' ', end='\n'):
        """Log a warning message."""
        self.print(*args, sep=sep, end=end, level=Log.WARNING)

    def error(self, *args, sep=' ', end='\n'):
        """Log an error message."""
        self.print(*args, sep=sep, end=end, level=Log.ERROR)

    @classmethod
    def code_to_level(cls, level_text):
        """
        Convert a log level name to its corresponding integer code.
        
        Parameters:
            level_text (str): The name of the log level (e.g., "INFO").
        
        Returns:
            int: The integer code for the log level.
        """
        try:
            return cls.levels.index(level_text)
        except ValueError:
            raise ValueError(f"Invalid log level name: {level_text}")
    

@dataclass
class Options():
    """
    A class to hold options parsed from the command line arguments.
    Default values are provided where applicable.
    """
    remove_work:        bool = False
    preserve_work:      bool = False
    verbose:            int  = 1
    log_level_file:     int  = Log.INFO
    log_level_console:  int  = Log.WARNING
    stdout_file:        str  = ""
    stderr_file:        str  = ""
    working_dir:        str  = ""
    log_file:           str  = ""
    target:             str  = ""
    tarball:            str  = ""
    args:               list = field(default_factory=list)

def path_is_parent(parent_path, child_path):
    """
    Checks if the given parent_path is a parent directory of child_path.
    
    Parameters:
        parent_path (str): The potential parent directory path.
        child_path (str): The potential child directory path.
        
    Returns:
        bool: True if parent_path is a parent of child_path, False otherwise.
    """
    parent_abs = os.path.abspath(parent_path)
    child_abs = os.path.abspath(child_path)
    return os.path.commonpath([parent_abs]) == os.path.commonpath([parent_abs, child_abs])


        

def test_tarball(log, tarball, working_dir):
    """
    Expands a tarball into the specified working directory and determines the project directory.
    
    Parameters:
        log: Logger instance for logging messages.
        tarball: Path to the tarball file to be expanded.
        working_dir: Directory where the tarball will be extracted.
        
    Returns:
        str: The path to the project directory, or None if an error occurs.
    """
    log.info(f"Expanding tarball: {tarball} into {working_dir}")
    project_dir = working_dir

    try:
        with tarfile.open(tarball, "r:gz") as tar:
            top_member = tar.getmembers()[0]
            if top_member.type == tarfile.DIRTYPE:
                project_dir = os.path.join(working_dir, top_member.name)
                log.info(f"Top level of the tarball is the directory: {top_member.name}")
            else:
                log.warning("Warning: top member of the tarball is not a directory. Rolling with it anyway.")
            tar.extractall(path=working_dir)
    except Exception as err:
        log.error(f"Error expanding the tarball: {err}")
        return None

    log.info(f"Project dir is set to: {project_dir}")
    return project_dir




def test_make(log, project_dir, stdout_file, stderr_file):
    """
    Runs the makefile in the specified project directory and captures stdout and stderr.

    Parameters:
        log: Logger instance for logging messages.
        project_dir: Directory containing the Makefile to execute.
        stdout_file: Path to the file where stdout will be written.
        stderr_file: Path to the file where stderr will be written.

    Returns:
        bool: True if the make command succeeds (return code 0), False otherwise.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        log.info("Running makefile")

        result = subprocess.run(["make"], capture_output=True, text=True)
        log_level = log.INFO if result.returncode == 0 else log.ERROR

        log.print(f"make returned code: {result.returncode}", level=log_level)
        log.print("stdout ---------------------", level=log_level)
        log.print(result.stdout.strip(), level=log_level)
        log.print("stderr ---------------------", level=log_level)
        log.print(result.stderr.strip(), level=log_level)

        return_code = result.returncode == 0

    except Exception as e:
        log.error(f"An error occurred while running make: {e}")
        return_code = False

    finally:
        os.chdir(original_cwd)

    try:
        with open(stdout_file, "w") as f:
            f.write(result.stdout)
        with open(stderr_file, "w") as f:
            f.write(result.stderr)
    except Exception as e:
        log.error(f"Failed to write stdout or stderr to files: {e}")
        return False

    return return_code


def test_readme(log, project_dir):
    """
    Checks if a README.txt file exists in the project directory and is not empty.
    
    Parameters:
        log: Logger instance for logging messages.
        project_dir: Directory where the README.txt file is expected to be located.
        
    Returns:
        bool: True if README.txt exists and is not empty, False otherwise.
    """
    readme_path = os.path.join(project_dir, "README.txt")

    try:
        stat = os.stat(readme_path)
        if stat.st_size == 0:
            log.error("README.txt exists but it is empty")
            return False
    except FileNotFoundError:
        log.error(f"README.txt not found in {project_dir}")
        return False
    except Exception as e:
        log.error(f"An error occurred while checking README.txt: {e}")
        return False

    return True

    

def test_target(log, project_dir, target):
    """
    Checks if a specified target file exists in the project directory.
    
    Parameters:
        log: Logger instance for logging messages.
        project_dir: Directory where the target file is expected to be located.
        target: Name of the target file to check.
        
    Returns:
        bool: True if the target file exists, False otherwise.
    """
    target_path = os.path.join(project_dir, target)

    try:
        os.stat(target_path)
    except FileNotFoundError:
        log.error(f"Target file '{target}' not found in {project_dir}")
        return False
    except Exception as e:
        log.error(f"An error occurred while checking target file '{target}': {e}")
        return False

    return True
    



def handle_args():
    """
    Processes command-line arguments and options, returning an Options object with the parsed values.
    
    Returns:
        Options: An object containing the processed command-line arguments and flags.
    """
    options = Options()
    
    try:
        opts, args = getopt.gnu_getopt(
            sys.argv[1:], 
            "vxo:e:hw:l:t:", 
            ["version", "stdout=", "stderr=", "help", "work=", "log=", "flog_level=", "clog_level=", "target="]
        )
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    options.working_dir = WORKING_DIR
    options.args        = args

    # Parse command-line options
    for opt, arg in opts:
        if opt == "-x":
            options.preserve_work = False
        elif opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-o", "--stdout"):
            options.stdout_file = arg
        elif opt in ("-e", "--stderr"):
            options.stderr_file = arg
        elif opt in ("-w", "--work"):
            options.working_dir = arg
        elif opt in ("-l", "--log"):
            options.log_file = arg
        elif opt in ("-v", "--version"):
            print( f"checkmake {VERSION}" );
            sys.exit(0)
        elif opt in ("-t", "--target"):
            options.target = arg
        elif opt in ("--flog_level", "--clog_level"):
            try:
                level = Log.code_to_level(arg)
                if opt == "--flog_level":
                    options.log_level_file = level
                else:
                    options.log_level_console = level
            except ValueError:
                print(f"Invalid log level: {arg}")
                sys.exit(1)
        else:
            raise ValueError(f"Unhandled option: {opt}")

    # Set default paths if not provided
    options.stdout_file = options.stdout_file or os.path.join(options.working_dir, STDOUT_FILE)
    options.stderr_file = options.stderr_file or os.path.join(options.working_dir, STDERR_FILE)
    options.log_file    = options.log_file    or os.path.join(options.working_dir, LOG_FILE)

    # Set tarball argument
    if not args:
        print("Error: Tarball argument is required.")
        sys.exit(1)
    options.tarball = args[0]

    return options

def usage():
    """
    Prints the usage information for the script, detailing the available options and arguments.
    """
    print(
        f"""
Usage: checkmake.py [OPTIONS] TARFILE
        
Version: {VERSION}

Options:
  -x                      Remove the working directory before starting (default: keep the directory).
  -w, --work=DIR          Specify the working directory where operations will be performed (default: ./work).
  -o, --stdout=FILE       File to write stdout output from the make process (default: {{working_dir}}/stdout.log).
  -e, --stderr=FILE       File to write stderr output from the make process (default: {{working_dir}}/stderr.log).
  -l, --log=FILE          File to write log messages (default: {{working_dir}}/logfile.log).
  -t, --target=FILE       Specify a target file to verify its presence in the project directory.
  --flog_level=LEVEL      Set the file logging level (e.g., DEBUG, INFO, WARNING, ERROR).
  --clog_level=LEVEL      Set the console logging level (e.g., DEBUG, INFO, WARNING, ERROR).
  -h, --help              Show this help message and exit.

Arguments:
  TARFILE                 The tarball file to be processed.

Examples:
  checkmake.py -w ./workdir -o stdout.log -e stderr.log my_tarball.tar.gz
  checkmake.py --stdout=stdout.log --stderr=stderr.log --work=./tmp my_tarball.tar.gz
        """
    )

def main():
    # Parse command-line arguments
    opts = handle_args()

    # Ensure the working directory is a child of the current directory
    if not path_is_parent(".", opts.working_dir):
        print(
            "The working directory must be a child of the current directory.\n"
            "This is to prevent accidental damage to your system."
        )
        sys.exit(1)

    # Clean up the working directory if not preserving it
    if not opts.preserve_work:
        shutil.rmtree(opts.working_dir, ignore_errors=True)

    # Create the working directory
    os.makedirs(opts.working_dir, exist_ok=True)

    # Initialize the logger
    log = Log(
        opts.log_file,
        log_level_console=opts.log_level_console,
        log_level_file=opts.log_level_file,
    )

    log.info("Starting the checks")

    # Expand the tarball
    project_dir = test_tarball(log, opts.tarball, opts.working_dir)
    if project_dir is None:
        log.error("Error in test_tarball: Failed to expand tarball")
        sys.exit(1)

    # Run the makefile
    if not test_make(log, project_dir, opts.stdout_file, opts.stderr_file):
        log.error("Error in test_make: Makefile execution failed")
        sys.exit(1)

    # Verify the README.txt file
    if not test_readme(log, project_dir):
        log.error("Error in test_readme: README.txt verification failed")
        sys.exit(1)

    # Check for the specified target, if provided
    if opts.target:
        if not test_target(log, project_dir, opts.target):
            log.error(f"Error in test_target: Target '{opts.target}' verification failed")
            sys.exit(1)

    # Remove the working directory if requested
    if not opts.remove_work:
        shutil.rmtree(opts.working_dir, ignore_errors=True)

    log.info("Process completed successfully")
    
if __name__ == "__main__":
    main()








        
