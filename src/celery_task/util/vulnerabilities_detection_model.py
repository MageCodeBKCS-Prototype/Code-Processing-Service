from torch import nn
import torch
from transformers import AutoTokenizer, AutoModel


class Branch(nn.Module):
    def __init__(self, input_size, hidden_size, dropout, num_outputs):
        super(Branch, self).__init__()

        self.dense1 = nn.Linear(input_size, hidden_size)
        self.batchnorm1 = nn.BatchNorm1d(hidden_size)
        self.dropout = nn.Dropout(p=dropout)
        self.dense2 = nn.Linear(hidden_size, num_outputs)

    def forward(self, x):
        out_dense1 = self.dense1(x)
        out_batchnorm1 = self.batchnorm1(out_dense1)
        out_dropout = self.dropout(out_batchnorm1)
        out_dense2 = self.dense2(out_dropout)

        return out_dense2


class BaseModel(nn.Module):
    def __init__(self, original_model, num_classes, is_multibranches=False):
        super(BaseModel, self).__init__()
        self.num_classes = num_classes
        self.original_model = original_model
        self.is_multibranches = is_multibranches
        branch_feature_size = 768
        if self.is_multibranches:
            self.branches = nn.ModuleList([Branch(branch_feature_size, 512, 0.1, 1) for _ in range(num_classes)])
        else:
            self.branch = Branch(branch_feature_size, 512, 0.2, num_classes)

        self.activation = nn.Sigmoid()

    def forward(self, inputs):
        out_bert = self.original_model(input_ids=inputs['input_ids'].squeeze().view(-1, 512),
                                       attention_mask=inputs['attention_mask'].squeeze().view(-1, 512))
        # pooler_out = torch.mean(out_bert.last_hidden_state,dim=1)
        pooler_out = out_bert.last_hidden_state[:, 0, :]
        if self.is_multibranches:
            output_branches = [branch(pooler_out) for branch in self.branches]
            out_branch = torch.cat(output_branches, dim=1)
        else:
            out_branch = self.branch(pooler_out)

        outputs = self.activation(out_branch)

        return outputs


def remove_prefix(state_dict, prefix):
    new_state_dict = {}
    for key in state_dict:
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            new_state_dict[new_key] = state_dict[key]
        else:
            new_state_dict[key] = state_dict[key]
    return new_state_dict


def get_model_tokenizer(device: str, model_name: str, model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    net = BaseModel(model, 4)

    checkpoint = torch.load(model_path, map_location=device)

    # Remove 'bc.' prefix
    new_model_state_dict = remove_prefix(checkpoint['model_state_dict'], 'module.')

    # print(new_model_state_dict)
    net.load_state_dict(new_model_state_dict)
    net.to(device)
    net.eval()

    print("Vulnerability tokenizer and model are ready")

    return tokenizer, net
