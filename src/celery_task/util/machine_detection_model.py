from torch import nn
import torch
from transformers import AutoTokenizer, AutoModel


class SimpleClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, model):
        super(SimpleClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()
        self.model = model
        for param in self.model.parameters():
            param.requires_grad = False

    def forward(self, x):
        x = self.model(input_ids=x['input_ids'].squeeze().view(-1, 512),
                       attention_mask=x['attention_mask'].squeeze().view(-1, 512))
        x = x.last_hidden_state[:, 0, :].squeeze()
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return x.squeeze()


def get_model_tokenizer(device: str, model_name: str, model_path: str):
    # load ai_model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    print("Model and Tokenizer loaded")

    checkpoint = torch.load(model_path)

    # Reinitialize the ai_model architecture
    classifier = SimpleClassifier(input_size=768, hidden_size=1024, output_size=1, model=model)

    # Load the saved parameters into the ai_model
    classifier.load_state_dict(checkpoint)
    classifier.to(device)
    classifier.eval()

    print("Classifier is ready")

    return tokenizer, classifier
