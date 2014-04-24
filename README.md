aws tools
=========

Tools for managing ipython notebooks on AWS clusters.

## Restart examples

Restart user001 notebook:

    python /home/molu8455/aws_tools/notebooks_restart.py -u 1
    python /home/molu8455/aws_tools/notebooks_restart.py -u molu8455

Restart all notebooks:
  
    python /home/molu8455/aws_tools/notebooks_restart.py
    
## Copy files

    python /home/molu8455/aws_tools/notebooks_copy.py -u 1 -d notebooks
    
output

    su user001 -c "mkdir -p /home/user001/notebooks"
    su user001 -c "cp -r /home/molu8455/notebooks/* /home/user001/notebooks/"
    
All users

    python /home/molu8455/aws_tools/notebooks_copy.py  -d notebooks
