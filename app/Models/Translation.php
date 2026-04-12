<?php

namespace App\Models;

use MongoDB\Laravel\Eloquent\Model;

class Translation extends Model
{
    protected $connection = 'mongodb';
    protected $collection = 'translations';

    protected $fillable = [
        'user_id',
        'file_id',
        'translated_text',
        'target_language'
    ];

    public function user()
    {
        return $this->belongsTo(User::class, 'user_id', '_id');
    }

    public function file()
    {
        return $this->belongsTo(File::class, 'file_id', '_id');
    }
}