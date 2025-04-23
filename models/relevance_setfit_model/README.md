---
tags:
- setfit
- sentence-transformers
- text-classification
- generated_from_setfit_trainer
widget:
- text: humans and morals over over profits is probably something you know absolutely
    nothing about. not only that costco is receiving an overwhelming amount of support.
    i personally just brought 5 annual memberships yesterday as gifts for family.
    → i would take that gift and burn it. → not all money is good money. costco knows
    that and the message of diversity, equality, and inclusion for everyone is worth
    a hell of a lot more than the greed and evil that is be pushed at them at this
    point.
- text: i bought them from costco, they are really useful i love them
- text: the two-step verification feature when recovering the account is unfair
- text: i love you, costco, for showing respect and commitment to your dei hires!
    i will always be a shopper at your store, and stop shopping at places that cave
    in to govt pressure.
- text: costco has great sparkling water
metrics:
- accuracy
- f1
- precision
- recall
pipeline_tag: text-classification
library_name: setfit
inference: true
base_model: sentence-transformers/all-MiniLM-L6-v2
model-index:
- name: SetFit with sentence-transformers/all-MiniLM-L6-v2
  results:
  - task:
      type: text-classification
      name: Text Classification
    dataset:
      name: Unknown
      type: unknown
      split: test
    metrics:
    - type: accuracy
      value: 0.96
      name: Accuracy
    - type: f1
      value: 0.9603553062178588
      name: F1
    - type: precision
      value: 0.9615808823529411
      name: Precision
    - type: recall
      value: 0.96
      name: Recall
---

# SetFit with sentence-transformers/all-MiniLM-L6-v2

This is a [SetFit](https://github.com/huggingface/setfit) model that can be used for Text Classification. This SetFit model uses [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) as the Sentence Transformer embedding model. A [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance is used for classification.

The model has been trained using an efficient few-shot learning technique that involves:

1. Fine-tuning a [Sentence Transformer](https://www.sbert.net) with contrastive learning.
2. Training a classification head with features from the fine-tuned Sentence Transformer.

## Model Details

### Model Description
- **Model Type:** SetFit
- **Sentence Transformer body:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **Classification head:** a [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance
- **Maximum Sequence Length:** 256 tokens
- **Number of Classes:** 2 classes
<!-- - **Training Dataset:** [Unknown](https://huggingface.co/datasets/unknown) -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Repository:** [SetFit on GitHub](https://github.com/huggingface/setfit)
- **Paper:** [Efficient Few-Shot Learning Without Prompts](https://arxiv.org/abs/2209.11055)
- **Blogpost:** [SetFit: Efficient Few-Shot Learning Without Prompts](https://huggingface.co/blog/setfit)

### Model Labels
| Label | Examples                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|:------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1     | <ul><li>'2016: "inclusivity is a core belief at target" → and notice they haven\'t even addressed it. "maybe no one will notice"! ha ha!'</li><li>'are you sure its not your dei policies? delta air lines'</li><li>'we got anti-semitic google before gtavi'</li></ul>                                                                                                                                                                                                                                                                                                                                                                |
| 0     | <ul><li>'when you will launch the stable version of gemini 2.0 pro ?!'</li><li>'im currently on board right now and hopefully we taking off soon with this delay i missed all my connect flights and cost me one day of my trip, my hotel, my car reservation etc. in thailand. i dont fly united airlines because of this problem with ou... see more → hello ,we are deeply sorry for making you feel that way, it was never our intention but we would like to closely look at the concern raised. please dm your reachable whatsapp number we connect you with an agent who can assist. thank you'</li><li>'sell outs!!'</li></ul> |

## Evaluation

### Metrics
| Label   | Accuracy | F1     | Precision | Recall |
|:--------|:---------|:-------|:----------|:-------|
| **all** | 0.96     | 0.9604 | 0.9616    | 0.96   |

## Uses

### Direct Use for Inference

First install the SetFit library:

```bash
pip install setfit
```

Then you can load this model and run inference.

```python
from setfit import SetFitModel

# Download from the 🤗 Hub
model = SetFitModel.from_pretrained("setfit_model_id")
# Run inference
preds = model("costco has great sparkling water")
```

<!--
### Downstream Use

*List how someone could finetune this model on their own dataset.*
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Set Metrics
| Training set | Min | Median | Max |
|:-------------|:----|:-------|:----|
| Word count   | 1   | 27.46  | 304 |

| Label | Training Sample Count |
|:------|:----------------------|
| 0     | 280                   |
| 1     | 120                   |

### Training Hyperparameters
- batch_size: (16, 16)
- num_epochs: (1, 1)
- max_steps: -1
- sampling_strategy: oversampling
- num_iterations: 20
- body_learning_rate: (2e-05, 2e-05)
- head_learning_rate: 2e-05
- loss: CosineSimilarityLoss
- distance_metric: cosine_distance
- margin: 0.25
- end_to_end: False
- use_amp: False
- warmup_proportion: 0.1
- l2_weight: 0.01
- seed: 42
- eval_max_steps: -1
- load_best_model_at_end: False

### Training Results
| Epoch | Step | Training Loss | Validation Loss |
|:-----:|:----:|:-------------:|:---------------:|
| 0.001 | 1    | 0.685         | -               |
| 0.05  | 50   | 0.3768        | -               |
| 0.1   | 100  | 0.2278        | -               |
| 0.15  | 150  | 0.1142        | -               |
| 0.2   | 200  | 0.0449        | -               |
| 0.25  | 250  | 0.0105        | -               |
| 0.3   | 300  | 0.0051        | -               |
| 0.35  | 350  | 0.0029        | -               |
| 0.4   | 400  | 0.002         | -               |
| 0.45  | 450  | 0.0015        | -               |
| 0.5   | 500  | 0.0014        | -               |
| 0.55  | 550  | 0.0012        | -               |
| 0.6   | 600  | 0.0011        | -               |
| 0.65  | 650  | 0.0009        | -               |
| 0.7   | 700  | 0.0009        | -               |
| 0.75  | 750  | 0.001         | -               |
| 0.8   | 800  | 0.0008        | -               |
| 0.85  | 850  | 0.0008        | -               |
| 0.9   | 900  | 0.0007        | -               |
| 0.95  | 950  | 0.0007        | -               |
| 1.0   | 1000 | 0.0007        | -               |

### Framework Versions
- Python: 3.10.16
- SetFit: 1.1.2
- Sentence Transformers: 4.1.0
- Transformers: 4.51.3
- PyTorch: 2.7.0
- Datasets: 3.5.0
- Tokenizers: 0.21.1

## Citation

### BibTeX
```bibtex
@article{https://doi.org/10.48550/arxiv.2209.11055,
    doi = {10.48550/ARXIV.2209.11055},
    url = {https://arxiv.org/abs/2209.11055},
    author = {Tunstall, Lewis and Reimers, Nils and Jo, Unso Eun Seo and Bates, Luke and Korat, Daniel and Wasserblat, Moshe and Pereg, Oren},
    keywords = {Computation and Language (cs.CL), FOS: Computer and information sciences, FOS: Computer and information sciences},
    title = {Efficient Few-Shot Learning Without Prompts},
    publisher = {arXiv},
    year = {2022},
    copyright = {Creative Commons Attribution 4.0 International}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->