import os
import shutil
import tempfile
from distutils.core import setup
from Cython.Build import cythonize

def compile_py_to_so(py_file_path, output_so_path):
    """
    Compile a Python .py file to a .so shared object file using Cython.
    
    Args:
        py_file_path (str): Path to the input .py file
        output_so_path (str): Path where the output .so file should be saved
    """
    # Create a temporary directory for build files
    temp_dir = tempfile.mkdtemp()
    try:
        # Get the base filename without extension
        module_name = os.path.splitext(os.path.basename(py_file_path))[0]
        
        # Setup arguments for compilation
        setup(
            ext_modules=cythonize(
                py_file_path,
                language_level="3",
                build_dir=temp_dir
            ),
            script_args=[
                'build_ext',
                '--inplace',
                '--build-lib', temp_dir,
                '--build-temp', temp_dir
            ]
        )
        
        # Find the generated .so file (it will be in the temp dir)
        generated_so = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.so') and module_name in file:
                    generated_so = os.path.join(root, file)
                    break
            if generated_so:
                break
                
        if not generated_so:
            raise RuntimeError("Compilation succeeded but no .so file was generated")
            
        # Move the .so file to the desired output location
        shutil.move(generated_so, output_so_path)
        
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Remove any generated .c files
        c_file = py_file_path.replace('.py', '.c')
        if os.path.exists(c_file):
            os.remove(c_file)
