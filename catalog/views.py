from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import permission_required
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import RenewBookForm
from .models import Author


def index(request):
   
    num_books=Book.objects.all().count()
    num_instances=BookInstance.objects.all().count()

    num_instances_available=BookInstance.objects.filter(status__exact='a').count()
    num_authors=Author.objects.count()
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {
        'num_books':num_books,
        'num_instances':num_instances,
        'num_instances_available':num_instances_available,
        'num_authors':num_authors,
        'num_visits':num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    context_object_name = 'my_book_list'
    template_name = 'catalog/book_list.html'  # <app>/<model>_list.html 
    paginate_by = 2

class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'book_detail.html'

class AuthorListView(generic.ListView):
    model = Author
    context_object_name = 'my_author_list'
    template_name = 'catalog/author_list.html'  # <app>/<model>_list.html 
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'author_detail.html'    

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('index')

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """
    Vista genérica basada en clases que enumera los libros prestados al usuario actual.
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """
    Vista genérica basada en clases que enumera TODOS los libros prestados (solo para bibliotecarios).
    Muestra el libro, el prestatario y la fecha de devolución.
    """
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})

class AuthorCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'',}

    def test_func(self):
        return self.request.user.is_staff

class AuthorUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

    def test_func(self):
        return self.request.user.is_staff

class AuthorDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

    def test_func(self):
        return self.request.user.is_staff

class BookCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    fields = '__all__'
    success_url = reverse_lazy('books')

    def test_func(self):
        return self.request.user.is_staff

class BookUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_staff

class BookDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')

    def test_func(self):
        return self.request.user.is_staff
