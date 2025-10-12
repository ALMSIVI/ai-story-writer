from pydantic import BaseModel


class LlmModel(BaseModel):
    provider: str
    name: str

    @classmethod
    def parse(cls, model_str: str) -> 'LlmModel':
        """
        Parses "<provider>.<name>" into a model object
        """
        try:
            index = model_str.index('.')
        except ValueError:
            # TODO: local model support
            raise ValueError(f'Failed to parse model {model_str}')

        return cls(provider=model_str[:index], name=model_str[index + 1 :])
