[![name](https://img.shields.io/pypi/v/juts?label=pypi%20package)](https://pypi.org/project/juts)
[![name](https://img.shields.io/pypi/dm/juts)](https://pypi.org/project/juts)

# Juts

Jupyter widgets for scheduling processes and visualizing the resulting
(live) data. While it is designed to use custom data-specific visualizations
(plot widgets) based on ipywidgets, visualizations for time series data
(bqplot), animations (matplotlib) and 3D data (ipyvolume) are included.

## Quickstart

To start a process a so-called job has to be set up. A job consists of a Python
function and a configuration. The function contains the code (machine learning,
simulation, ....) to be executed,
for [example](juts/examples/minimal_example.ipynb):

```
import time as tim
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

[Screencast min example.webm](https://github.com/riemarc/juts/assets/18379817/d711701a-4aea-4bd6-9d26-2e476c60b274)

Also live data can be monitored during script execution:

[Screencast min example live.webm](https://github.com/riemarc/juts/assets/18379817/c5ac1676-ceae-42ea-a652-8128c4e4c466)


## A simulation example

A more practical relevant [example](juts/examples/reaction_wheel.ipynb)
is the following simulation of a reaction wheel pendulum under state feedback
control.

[Screencast pendulum.webm](https://github.com/riemarc/juts/assets/18379817/f4cbbf97-d2cb-410d-a834-11c9422ddc27)

Widgets can be easily connected if required:

[Screencast pendulum link.webm](https://github.com/riemarc/juts/assets/18379817/e6342830-6258-4ca1-b8ed-0b1654e03444)

Since the simulation runs quite
fast, a loop was put after it which sends the data with a delay. This shows that
a job could also record live data from an experiment, so one could compare the
simulation data with the measurements from a real pendulum.

[Screencast pendulum live.webm](https://github.com/riemarc/juts/assets/18379817/dc0edbe0-8b5a-424a-91bf-eef0b944d14b)


## Visualizing 3D data

An example plot widget to view 3D data is also included, see
[heat_equation.ipynb](juts/examples/heat_equation.ipynb).
This one relies on [ipyvolume](https://github.com/widgetti/ipyvolume).

[Screencast 3d.webm](https://github.com/riemarc/juts/assets/18379817/762806cf-38b1-4f6d-ba5c-071bcbbcb9e2)
