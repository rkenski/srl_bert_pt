from allennlp_models.structured_prediction.predictors import SemanticRoleLabelerPredictor
from allennlp.predictors.predictor import Predictor
from allennlp.models import Model
from overrides import overrides
from allennlp.models.archival import load_archive
import my_model, my_reader, conll_reader
from allennlp.data import DatasetReader, Instance
from allennlp.common.util import JsonDict
import sys, os, json, torch
from typing import List, Iterator, Optional
from allennlp.commands.predict import _PredictManager
from allennlp.common.file_utils import cached_path
from nltk import tokenize, download
download('punkt')

import logging
logging.getLogger('allennlp').setLevel(logging.WARNING)

@Predictor.register("my_predictor")
class predict(SemanticRoleLabelerPredictor):
    def __init__(
        self, model: Model, dataset_reader: DatasetReader
    ) -> None:
        super().__init__(model, dataset_reader, spacy_model)

    @overrides
    def load_line(self, line: str) -> Iterator[str]:
        for sentence in tokenize.sent_tokenize(line):
            yield sentence

    @overrides
    def _json_to_instance(self, json_dict: JsonDict) -> Instance:
        new_sent=json_dict['sentence']
        tokens = self._tokenizer.tokenize(new_sent)
        return self.tokens_to_instances(tokens)
   
    @overrides
    def dump_line(self, outputs) -> str:
        output_file=open("output.txt", "a",encoding="utf-8")
        return json.dump(outputs, output_file,ensure_ascii=False)

    @overrides
    def _sentence_to_srl_instances(self, sentence):
        new_sent=""
        for char in sentence:
            new_sent+=char if char!="-" else " -"
        tokens = self._tokenizer.tokenize(new_sent)
        return self.tokens_to_instances(tokens)

    @overrides
    def predict_json(self, inputs: str):
        instances = self._sentence_to_srl_instances(inputs)
        if not instances:
            return inputs.split()
        return self.predict_instances(instances)

    @overrides
    def predict_instances(self, instances: List[Instance]) -> JsonDict:
        outputs = self._model.forward_on_instances(instances)
        results = {"verbs": [], "words": outputs[0]["words"]}
        for output in outputs:
            tags = output["tags"]
            description = self.make_srl_string(output["words"], tags)
            results["verbs"].append(
                {"verb": output["verb"], "description": description, "tags": tags}
            )
        return results



class predictManager(_PredictManager):
    def __init__(
        self,
        predictor: Predictor,
        input_file: str,
        output_file: Optional[str],
        batch_size: int,
        print_to_console: bool,
        has_dataset_reader: bool):
        super().__init__(predictor, input_file, output_file,batch_size,print_to_console, has_dataset_reader)

    @overrides
    def _get_json_data(self) -> Iterator[str]:
        if self._input_file == "-":
            for line in sys.stdin:
                if not line.isspace():
                    yield from self._predictor.load_line(line)
        else:
            input_file = cached_path(self._input_file)
            with open(input_file, "r", encoding="utf-8") as file_input:
                for line in file_input:
                    if not line.isspace():
                        yield from self._predictor.load_line(line)


if __name__ == "__main__":
    archive_file = sys.argv[1]
    input_text = sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) == 4 else "pt"
    if lang == "pt":
        spacy_model = "pt_core_news_sm"
    else:
        spacy_model = "en_core_web_sm"

    #esta é a função que demora
    archive = load_archive(
        archive_file,
        cuda_device = -1 #For CPU, otherwise use 'torch.cuda.current_device()'
    )

    if not os.path.isfile(input_text):
        f = open("tmp.txt", "w+", encoding="utf-8")
        f.write(input_text)
        input_text = "tmp.txt"
        f.close()


    predictor = Predictor.from_archive(
        archive, "my_predictor", dataset_reader_to_load="train"
    )

    manager = predictManager(predictor, input_text, None, 1, False, False)
    manager.run()

    if os.path.exists("tmp.txt"):
        os.remove("tmp.txt")

    with open("output.txt", "a") as f:
        f.write("\n")


archive_file = "ud_srl-enpt_xlmr-large"
input_text = 'esse é um texto de teste.'