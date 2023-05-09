[![name](https://img.shields.io/pypi/v/juts?label=pypi%20package)](https://pypi.org/project/juts)
[![name](https://img.shields.io/pypi/dm/juts)](https://pypi.org/project/juts)

# Juts

**Ju**pyter widgets for scheduling processes and visualizing the resulting (live) data.
While it is designed to use custom data-specific visualizations (plot widgets) based on
ipywidgets, visualizations for **t**ime **s**eries data (bqplot), animations
(matplotlib) and 3D data (ipyvolume) are included.

## Quickstart

To start a process a so called job has to be setup. A job consists of a python function and a configuration. The function contains the code (machine learning, simulation, ....) to be executed, for [example](juts/examples/minimal_example.ipynb):
```
def wait_n_times_x_ms(config, process_queue=None, return_dict=None):
    n = config["parameter"]["n"]
    x = config["parameter"]["x"]
    
    time = list()
    time_series = list()
    for i in range(n):
        time.append(i)
        time_series.append(i / x)
        
        process_queue.put(dict(progress=int(i/n * 100),
                               time=i,
                               time_series=i/x))
        tim.sleep(x)
```
The configuration(s) can be read from a yaml file like [this](juts/examples/wait_n_times_x_ms.yml):
```
wait_40_times_100_ms:
    parameter:
        n: 40
        x: 0.1
        
wait_10_times_300_ms:
    parameter:
        n: 10
        x: 0.3
```
or can be defined as python dictionary.

[Screencast min example.webm](https://github.com/riemarc/juts/assets/18379817/0fa83a34-cefd-4f1e-99e9-49642ab31963)

Also live data can be monitored during script execution:

[Screencast min example live.webm](https://github.com/riemarc/juts/assets/18379817/99211beb-424d-4841-bc71-953307306967)


## A simulation example

A more practical relevant example is the following simulation of a reaction
wheel pendulum under state feedback control.

[Screencast pendulum.webm](https://github.com/riemarc/juts/assets/18379817/3e8c9edc-12aa-496f-ba14-4c0adc677900)

Widgets can be easily connected, if required:

[Screencast pendulum link.webm](https://github.com/riemarc/juts/assets/18379817/cb8567b2-4ec8-4d9c-9f09-1cb466accbb7)

Since the simulation runs quite
fast, a loop was put after it which sends the data with a delay. This shows that
a job could also record live data from an experiment, so one could compare the
simulation data with the measurements from a real pendulum.

[Screencast pendulum live.webm](https://github.com/riemarc/juts/assets/18379817/f8759a47-58ba-43f3-8196-8e319ea82b65)
