conda create -n srl python=3.6
conda activate srl
pip install allennlp==1.2.2 allennlp_models==1.2.2
python get_model.py "ud_srl-enpt_xlmr-large"

