import copy
import datetime

class EvalConfig:
    def __init__(
        self,
        database_file: str,
        syncPara: SyncPara,
        cardPara: cardPara,
        run_slug: str,
        timeout: int = 1000
    ):
        self.database_file = database_file
        self.syncPara = syncPara
        self.cardPara = cardPara
        self.run_slug = run_slug
        self.dataframe = pd.DataFrame()
        self.timeout = timeout
    
    def copy():
        return copy.deepcopy(self)

class SyncPara():
    def __init__(self, alpha: float, beta: float, useMin: bool = True, useResIdent: bool = True):
        self.alpha = alpha
        self.beta = beta
        self.useMin = useMin
        self.useResIdent = useResIdent

class CardPara():
    def __init__(self, program: "opt" | "bound" | "both", threshold_opt: float, threshold_bound: float, method_bound: "minmax" | "iqr" | "quantiles"):
        self.program = program
        self.threshold_opt = threshold_opt
        self.threshold_bound = threshold_bound
        self.method_bound = method_bound


default_eval = EvalConfig(
    database_file="",
    run_slug="",
    syncPara=SyncPara(
        alpha=1.0,
        beta=1.0,
        useMin=True,
        useResIdent=True
    ),
    cardPara = CardPara(
        program="both",
        threshold_opt=0.2,
        threshold_bound=0.2,
        method_bound="minmax"
    )
)
datasets_stick = [
    "/mypath/"
]
datasets_laptop = [
    "/mypath/"
]
datasets = datasets_laptop

def run_discovery(config: EvalConfig):
    pass

def main():
    run_slug = f"{datetime.now().strftime("yymmdd_hhmm")}"
    for dataset in datasets:
        config = default_eval.copy()
        config.run_slug = slug
        config.database_file = dataset

        run_discovery


if __name__ == "__main__":
    main()
