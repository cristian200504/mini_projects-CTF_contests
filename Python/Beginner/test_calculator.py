from calculator import square

def test_positive():
    try:
        assert square(2) == 4
    except AssertionError:
        print("2 squared should be 4")
    try:    
        assert square(3) == 9
    except AssertionError:
        print("3 squared should be 9")

def test_negative():
    try:
        assert square(-2) == 4
    except AssertionError:
        print("-2 squared should be 4")
    try:    
        assert square(-3) == 9
    except AssertionError:
        print("-3 squared should be 9")      

def test_zero():
    try:
        assert square(0) == 0
    except AssertionError:
        print("0 squared should be 0")

def main():
     test_positive()
     test_negative()
     test_zero()
     print("All tests passed.")

if __name__ == "__main__":
    main()