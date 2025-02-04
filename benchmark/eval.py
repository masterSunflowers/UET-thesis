from fuzzywuzzy import fuzz


def cal_edit_sim(references, hypotheses):
    total = len(references)
    edit_sim = 0.0
    for pred, gt in zip(hypotheses, references):
        pred = pred.strip()
        gt = gt.strip()
        edit_sim += fuzz.ratio(pred, gt)
    return edit_sim / total


def cal_exactly_match(references, hypotheses):
    total = len(references)
    em = sum([pred.strip() == gt.strip() for pred, gt in zip(hypotheses, references)])
    return em / total
