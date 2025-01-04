import getopt
import os
import sys
import subprocess

tests = {
    "project.tar": 0,
    "project.tar.gz": 1,
    "project_build_error.tar.gz": 0,
    "project_empty_readme.tar.gz": 0,
    "project_no_dir.tar.gz": 1,
    "project_no_readme.tar.gz": 0
}

class Options():
    pass

def handle_args():
    options = Options()
    opts = []
    args = []

    options.target = ""
    
    try:
        opts, args = getopt.gnu_getopt( sys.argv[1:], "t:", [ "--target" ] )
    except getopt.GetoptError as err:
        print( err )
        sys.exit(1)

    options.test_dir = ""
    
    for o, a in opts:
        if o in ( "-t", "--target" ):
            options.target = a
        else:
            assert False, "unhandled option"


    if len(args) > 0:
        options.test_dir = args[0]

    return options

def main():
    opts = handle_args()

    for test in tests:
        test_path = "/".join( [ opts.test_dir, test ] )

        sys.stdout.write( "Testing " +  test + ": " )

        args = [ "python3", "checkmake.py", test_path ]
        if opts.target != "":
            args.extend( [ "--target", opts.target ] )

        result = subprocess.run( args, capture_output=True, text=True)

        rc = 1 if result.returncode == 0 else 0
        
        if tests[test] != rc:
            sys.stdout.write( "ERROR\n" )
        else:
            sys.stdout.write( "OK\n" )
                
                
        

if __name__ == "__main__":
    main()
