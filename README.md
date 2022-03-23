# Android App Fuzz Tester

Our tool is designed specifically for comparing the UI behavior of an app across different devices, different Android versions, 
and different app versions.
This tool allows Android app developers to easily perform backward and forward compatibility testing for their apps. It also 
enables a clear comparison between a stable version of app and a newer version of app. 
In doing so, it adapts multiple testing strategies and idea from [Mimic paper](https://dl.acm.org/doi/10.1109/ICSE.2019.00040) published at **_ICSE \`19_**.

<br/>

## How Does the Toool Work?

  <img src="https://github.com/ChangMinPark/android-fuzz-tester/blob/main/example/mimic.png" width="100%">

Our tool adapts the **_follow-the-leader_** design idea from **_Mimic_**, and above figure shows how Mimic runs. 

Just as Mimic, our tool takes as input a set of apps but not a script. Our system already includes pre-defined scripts in the main file, _main.py_. 
It runs on a desktop and runs configured tests on the set of devices connected via USB (also works with emulators). The tool is designed to be able 
to scale the number of apps tested as well as the number of devices used. Unlike Mimic provides a programming model and lets app developers to 
write a script, ours already pre-defined testing behaviors but still lets users to change testing modes and other configurations.

A tree figure on the right shows an example run. Using the **_follow-the-leader_** model, both versions execute the exact same sequence 
of UI events. For v1.0, the unvisited node (the Show button) is due to the run-time crash error that we inject; since the app crashes,
the button is not explored. For v1.1, the two unvisited nodes (the second Play button and the corresponding Stop button) are due to our 
leader-follower model; since the leader does not have those buttons, they are not explored in the follower. Using these graphs, 
testers can easily discover points of run- time errors as well as compare UI differences across different versions.

**_Important_** - Unlike Mimic, a tool in this repository is simplified version and does not support a programming model, visual inspections, and device resource evaluations such as a memory consumption and a battery power.

<br/>

## How to Use

### 1. Prepare Packages Required
> Install required python packages:
>  - **_uiautomator_**, **_pygraphviz_**, and **_networkx_**
>  
> If encounter an error while installing, run below command:
> ```sh
> $ sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config
> ```

### 2. Run


1. Run at least two emulators with different Android versions. 
2. Run the tester with APK path:
```sh
    $ python3 main.py test_apk
```
3. Select a leader device. 
4. After the test completely finishes, check the **_log_** directory for
the result and detailed information. 

### 3. Results

Results are stored under **_/log_** directory, and here are details of the results:


    log/
    ├── ...
    ├── date_time/                        # Date and time of the test
    │   ├── pkg_name/                     # Tested app package name
    |   |   ├── run_number/               # Each run number
    |   |   |   ├── adb_logcat.log        # ADB logcat while testing
    |   |   |   ├── ui_graph.log          # A graph of tested UIs
    |   |   |   └── uis_traversed.log     # A list of tested UIs 
    │   |   └── ...
    │   |── ...
    |   └-- results.log                       # Overall test results whether succeeded or failed
    └── ...

Here are am example UI graph generated after a test.

  <img src="https://github.com/ChangMinPark/android-fuzz-tester/blob/main/example/example_ui_graph.png" width="100%">
