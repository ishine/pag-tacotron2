from torch import nn
import torch

class Tacotron2Loss(nn.Module):
    def __init__(self, hparams):
        super(Tacotron2Loss, self).__init__()
        self.pos_weight = torch.tensor(hparams.gate_positive_weight)
        self.alignment_loss_scaler = hparams.alignment_loss_weight
        self.alignment_encoderwise_mean = hparams.alignment_encoderwise_mean
    
    def forward(self, model_output, targets):
        mel_target, gate_target, alignment_target = targets
        mel_target.requires_grad = False
        gate_target.requires_grad = False
        gate_target = gate_target.view(-1, 1)

        mel_out, mel_out_postnet, gate_out, alignment_out = model_output
        gate_out = gate_out.view(-1, 1)
        mel_loss = nn.MSELoss()(mel_out, mel_target) + \
            nn.MSELoss()(mel_out_postnet, mel_target)
        if self.alignment_encoderwise_mean:
            alignment_loss = nn.MSELoss()(alignment_out.transpose(1,2), alignment_target)
        else:
            alignment_loss = nn.MSELoss(reduction='sum')(alignment_out.transpose(1,2), alignment_target)
            alignment_loss = alignment_loss / (alignment_target.shape[0]*alignment_target.shape[2])
        gate_loss = nn.BCEWithLogitsLoss(pos_weight=self.pos_weight)(gate_out, gate_target)
        return mel_loss + gate_loss + (self.alignment_loss_scaler * alignment_loss), alignment_loss.item()
