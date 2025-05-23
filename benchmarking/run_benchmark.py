from ml.model import MLP_Model
import torch
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from benchmarking.heuristics import compute_heuristic_accuracy

# CONSTANTS

SIM_TEMPERATURE_FRACTIONS = np.round(np.arange(0.04, 1.60 + 0.04, 0.04), 6)

EXP_TO_CLASSIFIERS = {
    "al_fcc": ["Data-Centric Crystal Classifier", "Common Neighbor Analysis (Non-Diamond)", "Interval Common Neighbor Alaysis", "Ackland-Jones Analysis"],
    "li_bcc": ["Data-Centric Crystal Classifier", "Common Neighbor Analysis (Non-Diamond)", "Interval Common Neighbor Alaysis", "Ackland-Jones Analysis", "VoroTop Analysis"],
    "ti_hcp": ["Data-Centric Crystal Classifier", "Common Neighbor Analysis (Non-Diamond)", "Interval Common Neighbor Alaysis", "Ackland-Jones Analysis"],
    "ge_cd" : ["Data-Centric Crystal Classifier", "Common Neighbor Analysis (Diamond)", "Chill+"]
}

CORRECT_MAP_DC3 = {
    "al_fcc": 2,
    "li_bcc": 0,
    "ti_hcp": 3,
    "ge_cd" : 1
}

# MODEL

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = MLP_Model()
model.load_state_dict(torch.load("ml/models/model_2025-03-23_14-15-09.pt", map_location=device, weights_only=True))
model.to(device)
model.eval()

# BENCHMARKING

def run_benchmark(exp_name, classifiers):
    acc = {key : np.zeros_like(SIM_TEMPERATURE_FRACTIONS) for key in (classifiers + ["Data-Centric Crystal Classifier"])}

    for feature_file_name in os.listdir(f"md/features/{exp_name}"):
        # Get file info 
        sim_temp_id = feature_file_name[8:-3]
        idx = np.where(SIM_TEMPERATURE_FRACTIONS == float(sim_temp_id))[0][0]

        feature_path = f"md/features/{exp_name}/{feature_file_name}"
        raw_data_path = f"md/data/{exp_name}/dump_{sim_temp_id}.gz"

        for classifier in classifiers:
            # Do inference if it is DC3
            if classifier == "Data-Centric Crystal Classifier":
                # Get data
                data = torch.from_numpy(np.loadtxt(feature_path)).float()

                # Prediction
                with torch.no_grad():
                    preds = model(data.to(device)).argmax(dim=1).cpu()

                acc[classifier][idx] = (preds == CORRECT_MAP_DC3[exp_name]).sum().item() / len(preds)

            # Otherwise, run the heuristic
            else:
                acc[classifier][idx] = compute_heuristic_accuracy(exp_name, raw_data_path, classifier)

            print(f"T/T_m = {sim_temp_id} {classifier} accuracy: {acc[classifier][idx]}")

    # Convert accuracies to dataframe and save
    # The first column is SIM_TEMPERATURE_FRACTIONS and all other columns are accuracies of our methods
    df = pd.DataFrame(acc)
    df["T/T_m"] = SIM_TEMPERATURE_FRACTIONS
    df.set_index("T/T_m", inplace=True)
    df.to_csv(f"benchmarking/accuracies/{exp_name}.csv")

if __name__ == '__main__':
    # Only proccess selected experiments (if such are provided, otherwise proccess all)
    selected_experiments = None

    if len(sys.argv) > 1:
        selected_experiments = sys.argv[1:]
    
    for exp_name, classifiers in EXP_TO_CLASSIFIERS.items():
        if selected_experiments and exp_name not in selected_experiments:
            continue

        print(f"Running benchmark for {exp_name}")
        run_benchmark(exp_name, classifiers)