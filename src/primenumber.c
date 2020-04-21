#include <stdio.h>
#include <string.h>

int check_prime(int n)
{
    int i;
    for (i = 2; i * i <= n; i ++)
        if (n % i == 0) return 0;
    return 1;
}

int main(int argc, char **argv)
{
    int i, p;
    p = 0;
    int n = atoi(argv[1]);
    for (i = 100; i < n; ++ i)
         p += check_prime(i);

    printf("nprimes = %d\n", p);

    return 0;
}