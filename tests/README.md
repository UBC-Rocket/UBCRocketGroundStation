# Running Tests

## From PyCharm
To run the unit and integration tests from PyCharm, you need only add a new run configuration. Click the button in the top right and then click "Edit Configurations" in the dropdown menu. Go to Python > Python Tests > pytest and click "Create configuration". From there, set "Target" to "Script path" with "UBCRocketGroundStation/tests" as the directory. Now, whenever you need to run the test suite, just select pytest from the dropdown menu in the top right and run it as you normally would. This way of running tests supports the Debug and Concurrency modes if you require them.

## From the Command Line
To run pytest from the command line, simply run the `pytest` command. If you wish to see the output of every test, add the `--verbose` argument.

# Testing Best Practices

## Organization
* Every file's unit tests should be located in the /tests directory and named test_\<FileName\>.py.
* Any files containing expected data should be located in a directory within /tests with the same name as the test file that they are used in.
* Integration tests each get their own file in /tests/integration_tests.
* Unit tests for a class' methods should be in a class named Test\<ClassName\>. Unit tests for functions do not need to be put in classes
* Unit tests for functions and methods should be named test_\<FunctionName\>.
* Fixtures that are needed in multiple test classes or in test functions should be located at the top of the file (right under imports). Fixtures only needed in one class should be located in that class.

## Structure
* Inside each test, it is advised to separate code into three sections: setup, execution, and assertions.
  * Setup is where any constants not already defined in fixtures are defined and any necessary mocking is set up. It can be omitted if the test is simple enough or uses a fixture.
  * Execution is where the function or method is executed and its return value or any changed object variables are stored.
  * Assertion is where those stored values are compared to the expected value. This is usually done with an assert statement and the usual means of checking for equality. However, some data types, like numpy arrays, have their own methods for asserting equality (`numpy.testing.assert_array_equal(X, Y)`). Mocks also have their own assertions. It is generally best to limit the number of equality assertions in each test to one or two. Multiple values can be tested using parameterizations.

## Fixtures
* Pytest fixtures are generally preferable to setup and teardown methods, though setup and teardown methods are also acceptable.
* A simple fixture should be created if setup code is repeated in multiple test functions. Something like
  ```python
  def ubc_point_1():
      ubc_point_1 = MapBox.MapPoint(49.266904, -123.252976)
      return ubc_point_1
    ```
  is sufficient. Naturally, more advanced fixtures are required to replace setup and teardown methods.

## Mocking
* Mocking is necessary whenever a unit test needs to simulate more advanced functionality beyond its own scope, such as writing to a file.
* Although `unittest.mock` is compatible with Pytest, we are using `pytest-mock` for consistency. To use it, simply add `mocker` as a parameter to your test function or method. No imports are required.
* Mocking PyQt is rather difficult to do manually, so we are using `pytest-qt`. Just add `qtbot` as a parameter and it will take care of things automatically. There is also functionality to simulate button presses, if we decided to test at a higher layer in the future. As with `pytest-mock`, no imports are needed.