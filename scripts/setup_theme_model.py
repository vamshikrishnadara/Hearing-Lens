"""Install the same pinned embedding revision used by the cloud entrypoint."""

from scripts.model_setup import MODELS, install_model


def main():
    name = 'all-MiniLM-L6-v2'
    install_model(name)
    print(f'{name}: pinned revision {MODELS[name]["revision"]} is ready.', flush=True)


if __name__ == "__main__":
    main()
