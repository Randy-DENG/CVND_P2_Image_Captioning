import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        super(DecoderRNN, self).__init__()
        self.embed_size = embed_size
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        self.num_layers = num_layers
        self.hidden = 0
        # Add embedding layers to embed words
        self.word_embeddings = nn.Embedding(vocab_size, embed_size)
        # Add LSTM layer
        self.lstm = nn.LSTM(embed_size, hidden_size)
        # Add Linear layers to map hidden_size to vocab_size
        self.hidden2tag = nn.Linear(hidden_size, vocab_size)
    
    def forward(self, features, captions):
        # Initialize hidden state each forward step
        self.hidden = (torch.zeros(self.num_layers, features.shape[0], self.hidden_size), torch.zeros(self.num_layers, features.shape[0], self.hidden_size))
        # Transpose captions shape from [batch, seq_len] to [seq_len, batch]
        captions_transposed = captions.permute(1, 0)
        # Words embedding
        embeds = self.word_embeddings(captions_transposed)
        # Joint the features from images with the embedded captions, chape: [seq_len, batch, embed_size] 
        inputs = torch.cat([features.view(1, len(features), -1), embeds], 0)
        # Remove the last element: "<end>"
        inputs = inputs[:-1]
        # Pass inputs and hidden into LSTM
        lstm_out, self.hidden = self.lstm(inputs, self.hidden)
        # Pass into Linear layer
        tag_space = self.hidden2tag(lstm_out)
        # Softmax scores
        tag_scores = F.log_softmax(tag_space, dim=2)
        # Transpose tag_scores shape from [seq_len, batch, vocab_size] to [batch, seq_len, vocab_size]
        return tag_scores.permute(1, 0, 2)

    def sample(self, inputs, states=None, max_len=20):
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        pass