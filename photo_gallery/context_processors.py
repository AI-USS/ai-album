from .forms import ModelLearnForm


def learn_form(request):
    form = ModelLearnForm()
    return {
        'learn_form': form,
    }
