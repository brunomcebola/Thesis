import numpy as np
import matplotlib.pyplot as plt

PATHS_COMBINATIONS = {
    "Color Modality with RGB Inputs": {
        "Kinetics-I3D with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/color/kin400.rgb/scores.npy",
        "Kinetics-I3D with kinetics-400 + ImageNet checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/color/kin400_imagenet.rgb/scores.npy",
        "ViViT with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/vivit/checkpoints/color/kin400.rgb/scores.npy",
    },
    "Depth Modality with RGB Inputs": {
        "Kinetics-I3D with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/depth/kin400.rgb/scores.npy",
        "Kinetics-I3D with kinetics-400 + ImageNet checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/depth/kin400_imagenet.rgb/scores.npy",
        "ViViT with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/vivit/checkpoints/depth/kin400.rgb/scores.npy",
    },
    "Color Modality with Flow Inputs": {
        "Kinetics-I3D with kinetics-400 checkpoint for Flow": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/color/kin400.flow/scores.npy",
        "Kinetics-I3D with kinetics-400 + ImageNet checkpoint for Flow": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/color/kin400_imagenet.flow/scores.npy",
        "ViViT with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/vivit/checkpoints/color/kin400.flow/scores.npy",
    },
    "Depth Modality with Flow Inputs": {
        "Kinetics-I3D with kinetics-400 checkpoint for Flow": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/depth/kin400.flow/scores.npy",
        "Kinetics-I3D with kinetics-400 + ImageNet checkpoint for Flow": "/home/brunomcebola/Desktop/Thesis/models/models/kinetics/checkpoints/depth/kin400_imagenet.flow/scores.npy",
        "ViViT with kinetics-400 checkpoint for RGB": "/home/brunomcebola/Desktop/Thesis/models/models/vivit/checkpoints/depth/kin400.flow/scores.npy",
    },
}

scores_combinations = {}
for comb, paths in PATHS_COMBINATIONS.items():
    scores_combinations[comb] = {}

    for model, path in paths.items():
        hps_scores = np.load(path, allow_pickle=True).item() # type: ignore

        max_score = 0
        for hp, hp_scores in hps_scores.items():
            if np.max(hp_scores) > max_score:
                max_score = np.max(hp_scores)
                scores_combinations[comb][model] = hp_scores


plt.rc("font", size=20)
plt.rc("axes", titlesize=20)
plt.rc("axes", labelsize=20)
plt.rc("xtick", labelsize=20)
plt.rc("ytick", labelsize=20)
plt.rc("legend", fontsize=20)

for comb, scores in scores_combinations.items():
    _, axs = plt.subplots(1, 1, figsize=(20, 20))

    for model, score in scores.items():
        axs.plot(score, label=model)

    axs.set_title(f"{comb}")
    axs.set_xlabel("Epochs")
    axs.set_ylabel("Scores")
    axs.xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # type: ignore
    axs.set_yticks([i * 0.1 for i in range(11)])
    axs.set_ylim(0, 1)
    axs.set_xlim(left=0, right=100)
    axs.legend()
    axs.grid(True)

    plt.show()
