<?php

namespace App\Models;

use MongoDB\Laravel\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Tymon\JWTAuth\Contracts\JWTSubject;

class User extends Authenticatable implements JWTSubject
{
    use Notifiable;

    protected $connection = 'mongodb';
    protected $collection = 'users';

    // ✅ إضافة الحقول المطلوبة
    protected $fillable = [
        'name',
        'email',
        'password',
        'language',
        'theme',
        'avatar',           // ✅ إضافة حقل الصورة
        'avatar_url',       // ✅ إذا كنت تريد حفظ URL الصورة
        'created_at',       // ✅ إضافة تاريخ الإنشاء
        'updated_at',       // ✅ إضافة تاريخ التحديث
    ];

    protected $hidden = [
        'password',
    ];

    // ✅ إضافة dates للتأكد من التعامل مع التواريخ بشكل صحيح
    protected $dates = [
        'created_at',
        'updated_at',
    ];

    // JWT
    public function getJWTIdentifier()
    {
        return $this->getKey();
    }

    public function getJWTCustomClaims()
    {
        return [];
    }

    // ✅ إضافة accessor للحصول على URL الصورة الكامل
    public function getAvatarUrlAttribute()
    {
        if ($this->avatar && filter_var($this->avatar, FILTER_VALIDATE_URL)) {
            return $this->avatar;
        }
        
        if ($this->avatar) {
            return url('storage/avatars/' . $this->avatar);
        }
        
        return null;
    }

    // Relations
    public function files()
    {
        return $this->hasMany(File::class, 'user_id', '_id');
    }

    public function questions()
    {
        return $this->hasMany(Question::class, 'user_id', '_id');
    }

    public function summaries()
    {
        return $this->hasMany(Summary::class, 'user_id', '_id');
    }

    public function translations()
    {
        return $this->hasMany(Translation::class, 'user_id', '_id');
    }
}