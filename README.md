# Android App Fuzz Tester
This tetster tests multiple applications with fuzzing method. 
It first chooses one device as a leader and other rests as followers. 
For each test, it will install and test a single Android app on all the 
connected devices with exactly the same UI sequence. 

Users can change configurations on **_config.py_** file. (e.g., testing mode, 
sleep time, reboot option, etc.)


## Required Python3 Packages
- _networkx_
- _uiautomator_
- _pygraphviz_
  - If encounter an error while installing, run this:
    ```sh
    $ sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config
    ```

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
    ├── date_time                         # Date and time of the test
    │   ├── pkg_name                      # Tested app package name
    |   |   ├── run_number                # Each run number
    |   |   |   ├── adb_logcat.log        # ADB logcat while testing
    |   |   |   ├── ui_graph.log          # A graph of tested UIs
    |   |   |   └── uis_traversed.log     # A list of tested UIs 
    │   |   └── ...
    │   └── ...
    |── ...
    └── results.log                       # Overall test results whether succeeded or failed


