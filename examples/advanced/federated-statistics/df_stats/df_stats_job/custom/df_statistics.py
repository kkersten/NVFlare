# Copyright (c) 2022, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pandas.core.series import Series

from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.statistics_spec import BinRange, Feature, Histogram, HistogramType, Statistics
from nvflare.app_common.statistics.numpy_utils import dtype_to_data_type, get_std_histogram_buckets


class DFStatistics(Statistics):
    def __init__(self, data_path):
        super().__init__()
        self.data_root_dir = "/tmp/nvflare/data"
        self.data_path = data_path
        self.data: Optional[Dict[str, pd.DataFrame]] = None
        self.data_features = [
            "Age",
            "Workclass",
            "fnlwgt",
            "Education",
            "Education-Num",
            "Marital Status",
            "Occupation",
            "Relationship",
            "Race",
            "Sex",
            "Capital Gain",
            "Capital Loss",
            "Hours per week",
            "Country",
            "Target",
        ]
        self.skip_rows = {
            "site-1": [],
            "site-2": [0],
        }

    def load_data(self, fl_ctx: FLContext) -> Dict[str, pd.DataFrame]:
        client_name = fl_ctx.get_identity_name()
        self.log_info(fl_ctx, f"load data for client {client_name}")
        try:
            skip_rows = self.skip_rows[client_name]
            data_path = f"{self.data_root_dir}/{fl_ctx.get_identity_name()}/{self.data_path}"
            # example of load data from CSV
            df: pd.DataFrame = pd.read_csv(
                data_path, names=self.data_features, sep=r"\s*,\s*", skiprows=skip_rows, engine="python", na_values="?"
            )
            train = df.sample(frac=0.8, random_state=200)  # random state is a seed value
            test = df.drop(train.index).sample(frac=1.0)

            self.log_info(fl_ctx, f"load data done for client {client_name}")
            return {"train": train, "test": test}

        except BaseException as e:
            raise Exception(f"Load data for client {client_name} failed! {e}")

    def initialize(self, fl_ctx: FLContext):
        self.data = self.load_data(fl_ctx)
        if self.data is None:
            raise ValueError("data is not loaded. make sure the data is loaded")

    def features(self) -> Dict[str, List[Feature]]:
        results: Dict[str, List[Feature]] = {}
        for ds_name in self.data:
            df = self.data[ds_name]
            results[ds_name] = []
            for feature_name in df:
                data_type = dtype_to_data_type(df[feature_name].dtype)
                results[ds_name].append(Feature(feature_name, data_type))

        return results

    def count(self, dataset_name: str, feature_name: str) -> int:
        df: pd.DataFrame = self.data[dataset_name]
        return df[feature_name].count()

    def sum(self, dataset_name: str, feature_name: str) -> float:
        df: pd.DataFrame = self.data[dataset_name]
        return df[feature_name].sum().item()

    def mean(self, dataset_name: str, feature_name: str) -> float:

        count: int = self.count(dataset_name, feature_name)
        sum_value: float = self.sum(dataset_name, feature_name)
        return sum_value / count

    def stddev(self, dataset_name: str, feature_name: str) -> float:
        df = self.data[dataset_name]
        return df[feature_name].std().item()

    def variance_with_mean(
        self, dataset_name: str, feature_name: str, global_mean: float, global_count: float
    ) -> float:
        df = self.data[dataset_name]
        tmp = (df[feature_name] - global_mean) * (df[feature_name] - global_mean)
        variance = tmp.sum() / (global_count - 1)
        return variance.item()

    def histogram(
        self, dataset_name: str, feature_name: str, num_of_bins: int, global_min_value: float, global_max_value: float
    ) -> Histogram:

        num_of_bins: int = num_of_bins

        df = self.data[dataset_name]
        feature: Series = df[feature_name]
        flattened = feature.ravel()
        flattened = flattened[flattened != np.array(None)]
        buckets = get_std_histogram_buckets(flattened, num_of_bins, BinRange(global_min_value, global_max_value))
        return Histogram(HistogramType.STANDARD, buckets)

    def max_value(self, dataset_name: str, feature_name: str) -> float:
        """this is needed for histogram calculation, not used for reporting"""

        df = self.data[dataset_name]
        return df[feature_name].max()

    def min_value(self, dataset_name: str, feature_name: str) -> float:
        """this is needed for histogram calculation, not used for reporting"""

        df = self.data[dataset_name]
        return df[feature_name].min()
