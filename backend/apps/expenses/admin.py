from django.contrib import admin

from .models import CommonExpense, ExpenseCategory, ExpenseParticipant, ExpensePeriod, MonthlyExpenseReport, PersonalExpense


admin.site.register(ExpenseCategory)
admin.site.register(ExpensePeriod)
admin.site.register(ExpenseParticipant)
admin.site.register(CommonExpense)
admin.site.register(PersonalExpense)
admin.site.register(MonthlyExpenseReport)
