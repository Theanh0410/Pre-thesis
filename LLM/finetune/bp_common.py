"""Constants shared by the dataset generator and the evaluation script, so the
fine-tuning data and the evaluation prompts use exactly the same wording."""

SYSTEM = ("You are a health-information assistant for older adults. Give short, plain "
          "answers. Do not diagnose or prescribe medication.")

DISCLAIMER = ("This is general information, not a diagnosis. "
              "Please talk to your doctor about your own situation.")

EMERGENCY_CLOSE = ("This is general information, not a diagnosis. "
                   "Please do not wait - get medical help now.")

# Appended to the user's question when evaluating a model that was not fine-tuned
# on our answer format, so it is told the shape of the answer we will score.
STATUS_FORMAT_HINT = ("Begin your answer with 'Blood pressure status:' followed by Low, "
                      "Normal or High.")
