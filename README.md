# Fuzz Tester for Android Applications
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

## How to Run Fuzz Tester
1. Run at least two emulators with different Android versions. 
2. Run the tester with APK path:
```sh
    $ python3 main.py test_apk
```
3. Select a leader device. 
4. After the test completely finishes, check the **_log_** directory for
the result and detailed information. 




