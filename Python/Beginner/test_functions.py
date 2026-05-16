from functions import hello

def test_hello():
    assert hello("Alice") == "Hello Alice"
    assert hello("Bob") == "Hello Bob" 

def test_hello_default():
    assert hello() == "Hello World"

def main():
    test_hello()
    test_hello_default()
    print("All tests passed!")

if __name__ == "__main__":
    main()