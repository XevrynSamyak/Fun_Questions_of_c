#include <stdio.h>
#include <string.h>
int main(){
    char item[20];
    float price,sum =0;
    int number_of_items,i,a;

    printf("number of items: ");
    scanf("%d",&a);
    getchar();

    for(i=0;i<a;i++){
     printf("enter the item you want:\n ");
     fgets(item,sizeof(item),stdin);

     printf("enter the number of item you want: ");
     scanf("%d",&number_of_items);

     printf("enter price of the item: ");
     scanf("%f",&price);
     
     getchar();

     sum += price * number_of_items;
    }
    register float total = sum;
    printf("total: %.2f",total);

}