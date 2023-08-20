from ISS.hooks import HookManager, Catch

def profile_catch_generator(poster):
    return {
        'poster': poster
    }

HookManager.register_catch(Catch(
    'user_profile_stats',
    profile_catch_generator,
    'taboo/user_profile_stats.html'))

