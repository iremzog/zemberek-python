from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .single_analysis import SingleAnalysis


class WordAnalysis:
    EMPTY_INPUT_RESULT: 'WordAnalysis' = None

    def __init__(self, inp: str, analysis_results: Tuple['SingleAnalysis', ...], normalized_input: str = None):
        self.inp = inp
        self.analysis_results = analysis_results
        self.normalized_input = self.inp if normalized_input is None else normalized_input
        self.index = 0

    def is_correct(self) -> bool:
        return len(self.analysis_results) > 0 and not self.analysis_results[0].is_unknown()

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, WordAnalysis):
            if self.inp != other.inp:
                return False
            else:
                return False if self.normalized_input != other.normalized_input else \
                    self.analysis_results == other.analysis_results
        else:
            return False

    def __hash__(self):
        result = hash(self.inp)
        result = 31 * result + hash(self.normalized_input)
        for x in self.analysis_results:
            result = 31 * result + (hash(x) if x else 0)
        return result

    def __str__(self):
        return "WordAnalysis{input='" + self.inp + '\'' + ", normalizedInput='" + self.normalized_input + '\'' + \
               ", analysisResults=" + ' '.join([str(a) for a in self.analysis_results]) + '}'

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.analysis_results):
            result = self.analysis_results[self.index]
            self.index += 1
            return result
        raise StopIteration


WordAnalysis.EMPTY_INPUT_RESULT = WordAnalysis("", ())
