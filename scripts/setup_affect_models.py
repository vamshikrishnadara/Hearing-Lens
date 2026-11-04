"""Install the same pinned affect revisions used by the cloud entrypoint."""
from scripts.model_setup import MODELS, install_model


def main():
    for kind in ('sentiment', 'emotion'):
        install_model(kind)
        print(f'{kind}: pinned revision {MODELS[kind]["revision"]} is ready.', flush=True)


if __name__ == '__main__':
    main()
