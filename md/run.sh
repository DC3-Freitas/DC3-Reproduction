#!/bin/bash
#SBATCH --job-name=MD_SIM_AR
#SBATCH --ntasks 16
#SBATCH --nodes 1
#SBATCH --time 1:00:00

#SBATCH --partition sched_mit_rodrigof_r8
#SBATCH --mem-per-cpu=8000
#SBATCH --output output.txt
# Load any necessary modules
source ~/.bashrc
# Activate your Conda environment
conda activate lammps_env
mpirun -np 4 lmp -in Ar.in
