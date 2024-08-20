## /bin/zsh


### This is a guide to install the required packages to run the Python Mojo example


#### Install updates

```zsh
sudo apt-get update
```

#### Install packages
```zsh
sudo apt-get install curl
sudo apt-get install llvm
```

#### Install python3.8

```zsh
sudo apt-get install python3.8
sudo apt-get install python3.8-venv
```

#### Create a virtual environment

```zsh
python3.8 -m venv venv
source venv/bin/activate
```

#### Install the required packages

```zsh
pip install -r requirements.txt
```

#### Install Mojo

```zsh
curl -s https://get.modular.com | sh -s -- a3cfc72b-12bc-4157-9160-fd849dda6566
```

#### Install the MAX SDK (it includes Mojo)
```zsh
modular install max
```

#### Install the MAX Engine Python package

```zsh
MAX_PATH=$(modular config max.path) && python3.8 -m pip install --find-links $MAX_PATH/wheels max-engine
```

#### If you're using ZSH, run this command

```zsh
MAX_PATH=$(modular config max.path) \
  && echo 'export MODULAR_HOME="'$HOME'/.modular"' >> ~/.zshrc \
  && echo 'export PATH="'$MAX_PATH'/bin:$PATH"' >> ~/.zshrc \
  && source ~/.zshrc
```

#### Set up the environment variables
```zsh
export MOJO_PYTHON=python3.8
export MOJO_PYTHON_LIBRARY=$(python3.8 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
export PYTHONEXECUTABLE=$(which python3.8)
```

