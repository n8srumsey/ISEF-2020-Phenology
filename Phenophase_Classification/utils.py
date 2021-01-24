K = 5
EPOCHS = 50
BATCH_SIZE = 384
TRANSFORM = True
NB_TRANSFORMATIONS = 16
EFFECTIVE_BATCH_SIZE = int(BATCH_SIZE / NB_TRANSFORMATIONS)

DATA_DIR = './Phenophase_Classification/data/'
IMAGES_DIR = './Phenophase_Classification/data/images/'
RESULTS_DIR = './Phenophase_Classification/results/'
MODELS_DIR = './Phenophase_Classification/models/'