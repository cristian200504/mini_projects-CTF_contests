public class Animal
{
    protected String name;
    protected String species;
    public Animal(String name, String species)
    {
        this.name = name;
        this.species = species;
    }
    @Override
    public String toString()
    {
        return "Animal{name='" + name + "', species='" + species + "'}";
    }
}
