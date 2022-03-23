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

Just as Mimic, our tool takes a set of apps as input but not a script. Our system already includes pre-defined scripts in the main file, _main.py_. 
It runs on a desktop and runs configured tests on the set of devices connected via USB (also works with emulators). The tool is designed to be able 
to scale the number of apps tested as well as the number of devices used. Unlike Mimic provides a programming model and lets app developers to 
write a script, ours already pre-defined testing behaviors but still lets users to change testing modes and other configurations. The main 
mode, **_follow-the-leader_** model is choosing one device as a leader and others to follower devices. This lets fuzz-tester (randomly choose UIs) 
to test same UIs on follower devices as the leader and makes easier to find exactly where in a UI tree has compatibility issues. 

A tree figure on the right shows an example run. Using the **_follow-the-leader_** model, both versions execute the exact same sequence 
of UI events. For v1.0, the unvisited node (the Show button) is due to the run-time crash error that we inject; since the app crashes,
the button is not explored. For v1.1, the two unvisited nodes (the second Play button and the corresponding Stop button) are due to our 
leader-follower model; since the leader does not have those buttons, they are not explored in the follower. Using these graphs, 
testers can easily discover points of run-time errors as well as compare UI differences across different versions.

For more details, please read the paper. 

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
1. Set configurations as you prefer. Here are configurations that can be set.
    > **_RANDOM_** - on each screen, choose UIs randomly or test all UIs thoroughly
    >
    > **_FOLLOW_LEADER_** - whether to run in follow-the-leader mode
    >
    > **_REBOOT_** - whether to reboot devices after done testing with each app (to reset device state)
    >
    > **_KEEP_INSTALLED_** - whether to delete and reinstall an app after each test (for login-required app)
    >
    > **_NUM_RUNS_** - a number of test runs per app 
    > 
    > **_TESTING_TIME_** - how long to test for each run

2. Connect Android devices or run emulators to test on.

3. Run with an app path (or directory). If a directory, test all apps recursively found.
    ```sh
    $ python3 main.py example/example_app.apk
    ```

4. When a list connected devices is shown, choose which device to choose as a leader (in **_follow-the-leader mode_**):
    ```text
    List of devices running:
      0. emulator-5554 (Android 8.1.0)
      1. emulator-5556 (Android 10)
    
    Which device would you like to select for a leader (# or serial)? 
    ```

5. Below screenshots is an example log written while testing. 

    <img src="https://github.com/ChangMinPark/android-fuzz-tester/blob/main/example/log.png" width="600">



### 3. Results

Results are stored under **_log/_** directory, and here are details of the results:


    log/
    ├── ...
    ├── date_time/                            # Date and time of the test
    │   ├── pkg_name/                         # Tested app package name
    |   |   ├── run_number/                   # Each run number
    |   |   |   ├── adb_logcat.log            # ADB logcat while testing
    |   |   |   ├── ui_graph.log              # A graph of tested UIs
    |   |   |   └── uis_traversed.log         # A list of tested UIs 
    │   |   └── ...
    │   |── ...
    |   └-- results.log                       # Overall test results whether succeeded or failed
    └── ...

Here is an example UI graph generated after a test.

  <img src="https://github.com/ChangMinPark/android-fuzz-tester/blob/main/example/example_ui_graph.png" width="100%">
