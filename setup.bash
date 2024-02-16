conda create -n srl python=3.6
conda activate srl
pip install allennlp==1.2.2 allennlp_models==1.2.2 overrides==3.1.0
pip install tensorboardx==2.2
pip install transformers --ignore-installed certifi
python get_model.py "ud_srl-enpt_xlmr-large"

