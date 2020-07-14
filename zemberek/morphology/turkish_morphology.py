from __future__ import annotations

import time
import logging

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tokenization.token import Token
    from .analysis.single_analysis import SingleAnalysis

from zemberek.tokenization import TurkishTokenizer
from zemberek.core.turkish import TurkishAlphabet, StemAndEnding, PrimaryPos
from zemberek.core.text import TextUtil
from .analysis.word_analysis import WordAnalysis
from .analysis.rule_based_analyzer import RuleBasedAnalyzer
from .analysis.unidentified_token_analyzer import UnidentifiedTokenAnalyzer
from .generator import WordGenerator
from .lexicon import RootLexicon
from .morphotactics import TurkishMorphotactics, InformalTurkishMorphotactics

logger = logging.getLogger(__name__)


class TurkishMorphology:
    """
    private RootLexicon lexicon;
    private RuleBasedAnalyzer analyzer;
    private WordGenerator wordGenerator;
    private UnidentifiedTokenAnalyzer unidentifiedTokenAnalyzer;
    private TurkishTokenizer tokenizer;
    private AnalysisCache cache;
    private TurkishMorphotactics morphotactics;
    private AmbiguityResolver ambiguityResolver;
    private boolean useUnidentifiedTokenAnalyzer;
    private boolean useCache;
    """

    def __init__(self, builder: 'TurkishMorphology.Builder'):
        self.lexicon = builder.lexicon
        self.morphotactics = InformalTurkishMorphotactics(self.lexicon) if builder.informal_analysis \
            else TurkishMorphotactics(self.lexicon)
        self.analyzer = RuleBasedAnalyzer.ignore_diacritics_instance(self.morphotactics) if \
            builder.ignore_diacritics_in_analysis else RuleBasedAnalyzer.instance(self.morphotactics)
        self.unidentified_token_analyzer = UnidentifiedTokenAnalyzer(self.analyzer)
        self.tokenizer = builder.tokenizer
        self.word_generator = WordGenerator(self.morphotactics)

        self.use_cache = builder.use_dynamic_cache
        self.use_unidentified_token_analyzer = builder.use_unidentifiedTokenAnalyzer
        # DEVAM EDEBILIR

    @staticmethod
    def builder(lexicon: RootLexicon) -> 'TurkishMorphology.Builder':
        return TurkishMorphology.Builder(lexicon)

    @staticmethod
    def create_with_defaults() -> 'TurkishMorphology':
        start_time = time.time()
        instance = TurkishMorphology.Builder(RootLexicon.get_default()).build()
        logger.info(f"Initialized in {time.time() - start_time}")
        return instance

    def analyze(self, word: str) -> WordAnalysis:
        return self.analyze_with_cache(word) if self.use_cache else self.analyze_without_cache(word=word)

    def analyze_with_cache(self, word: str) -> WordAnalysis:
        raise NotImplementedError('Cache is not implemented yet, make use_cache False')

    @staticmethod
    def normalize_for_analysis(word: str) -> str:
        s = word.translate(TurkishAlphabet.INSTANCE.lower_map).lower()
        s = TurkishAlphabet.INSTANCE.normalize_circumflex(s)
        no_dot = s.replace(".", "")
        if len(no_dot) == 0:
            no_dot = s

        return TextUtil.normalize_apostrophes(no_dot)

    def analyze_without_cache(self, word: str = None, token: Token = None) -> WordAnalysis:
        if word:
            tokens: List[Token] = self.tokenizer.tokenize(word)
            return WordAnalysis(word, (), normalized_input=word) if len(tokens) != 1 else \
                self.analyze_without_cache(token=tokens[0])
        else:  # token is not None
            word = token.content  # equal to token.getText()
            s = self.normalize_for_analysis(word)
            if len(s) == 0:
                return WordAnalysis.EMPTY_INPUT_RESULT
            else:
                if TurkishAlphabet.INSTANCE.contains_apostrophe(s):
                    s = TurkishAlphabet.INSTANCE.normalize_apostrophe(s)
                    result = self.analyze_words_with_apostrophe(s)
                else:
                    result = self.analyzer.analyze(s)

                if len(result) == 0 and self.use_unidentified_token_analyzer:
                    result = self.unidentified_token_analyzer.analyze(token)

                if len(result) == 1 and result[0].item.is_unknown():
                    result = ()

                return WordAnalysis(word, normalized_input=s, analysis_results=result)

    def analyze_words_with_apostrophe(self, word: str) -> Tuple[SingleAnalysis, ...]:
        index = word.find(chr(39))
        if index > 0 and index != len(word) - 1:
            se = StemAndEnding(word[0:index], word[index + 1:])
            stem = TurkishAlphabet.INSTANCE.normalize(se.stem)
            without_quote = word.replace("'", "")
            no_quotes_parses = self.analyzer.analyze(without_quote)
            return () if len(no_quotes_parses) == 0 else \
                tuple(p for p in no_quotes_parses if p.item.primary_pos == PrimaryPos.Noun and
                      (p.contains_morpheme(TurkishMorphotactics.p3sg) or p.get_stem() == stem))
        else:
            return ()

    class Builder:
        """
        RootLexicon lexicon = new RootLexicon();
        boolean useDynamicCache = true;
        boolean useUnidentifiedTokenAnalyzer = true;
        AnalysisCache cache;
        AmbiguityResolver ambiguityResolver;
        TurkishTokenizer tokenizer;
        boolean informalAnalysis;
        boolean ignoreDiacriticsInAnalysis;
        """

        use_dynamic_cache = False  # THIS CAN BE CONVERTED TO TRUE IF CACHE IS TO BE IMPLEMENTED
        use_unidentifiedTokenAnalyzer = True

        def __init__(self, lexicon: RootLexicon):
            self.tokenizer = TurkishTokenizer.DEFAULT
            self.lexicon = lexicon
            self.informal_analysis = False
            self.ignore_diacritics_in_analysis = False

        def set_lexicon(self, lexicon: RootLexicon) -> 'TurkishMorphology.Builder':
            self.lexicon = lexicon
            return self

        def use_informal_analysis(self) -> 'TurkishMorphology.Builder':
            self.informal_analysis = True
            return self

        def ignore_diacritics_in_analysis_(self) -> 'TurkishMorphology.Builder':
            self.ignore_diacritics_in_analysis = True
            return self

        def build(self) -> 'TurkishMorphology':
            return TurkishMorphology(self)
