# Juts

**Ju**pyter widgets for scheduling processes and visualizing the resulting (live) data.
While it is designed to use custom data-specific visualizations based on
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
[Screencast from 09.05.2023 13:35:58.webm](https://github.com/riemarc/juts/assets/18379817/e0aae907-8cf1-4958-9e8e-42dc5024e16a)
Also live data can be monitored during script execution:
[Screencast from 09.05.2023 13:37:38.webm](https://github.com/riemarc/juts/assets/18379817/bc3878a8-29fa-457f-b6f8-3287c849405e)
